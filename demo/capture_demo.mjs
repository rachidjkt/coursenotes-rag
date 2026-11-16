// Optional screenshot check using Node's built-in CDP client and an existing Chrome.
// No npm packages, downloads, fabricated responses, or video generation.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const browserPath = process.env.CHROME_PATH || path.join(process.env.LOCALAPPDATA || '', 'ms-playwright/chromium-1228/chrome-win64/chrome.exe');
const appURL = process.env.DEMO_URL || 'http://127.0.0.1:8502';
if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(appURL)) throw Error('Use a loopback demo URL.');
if (!fs.existsSync(browserPath)) throw Error('Set CHROME_PATH to an existing Chrome executable; no browser is downloaded.');
const output = path.join(root, 'docs/demo');
fs.mkdirSync(output, {recursive:true});
const browser = spawn(browserPath, ['--headless=new', '--remote-debugging-port=9337',
  '--remote-debugging-address=127.0.0.1', `--user-data-dir=${path.join(root,'.browser_profile')}`,
  '--no-first-run', '--no-default-browser-check', 'about:blank'], {windowsHide:true, stdio:'ignore'});
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
let browserConnection;

async function connect(url) {
  const ws = new WebSocket(url);
  await new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>reject(Error('DevTools connection timeout')),10000);
    ws.onopen=()=>{clearTimeout(timeout);resolve();};
    ws.onerror=error=>{clearTimeout(timeout);reject(error);};
  });
  let id = 0;
  const pending = new Map();
  ws.onmessage = ({data})=>{
    const message=JSON.parse(data);
    if (!message.id) return;
    const entry=pending.get(message.id);
    if (!entry) return;
    pending.delete(message.id);
    message.error ? entry.reject(Error(JSON.stringify(message.error))) : entry.resolve(message.result);
  };
  return {close:()=>ws.close(), call:(method,params={})=>new Promise((resolve,reject)=>{
    const request=++id;pending.set(request,{resolve,reject});ws.send(JSON.stringify({id:request,method,params}));
    setTimeout(()=>{if(pending.delete(request))reject(Error('CDP timeout: '+method));},30000).unref();
  })};
}

try {
  let version;
  for(let attempt=0;attempt<100;attempt++) {
    try {version=await (await fetch('http://127.0.0.1:9337/json/version')).json();break;} catch {await delay(200);}
  }
  if(!version)throw Error('Chrome did not start.');
  console.log('Chrome ready');
  browserConnection=await connect(version.webSocketDebuggerUrl);
  const {targetId}=await browserConnection.call('Target.createTarget',{url:'about:blank'});
  console.log('Created browser target');
  const targets=await (await fetch('http://127.0.0.1:9337/json/list')).json();
  const page=await connect(targets.find(t=>t.id===targetId).webSocketDebuggerUrl);
  console.log('Connected page');
  await page.call('Page.enable');
  console.log('Page enabled');
  await page.call('Runtime.enable');
  console.log('Runtime enabled');
  await page.call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
  await page.call('Page.navigate',{url:appURL});
  console.log('Navigated to local app');
  const evaluate=async expression=>{
    const result=await page.call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  async function waitFor(expression,timeout=180000) {
    const end=Date.now()+timeout;
    while(Date.now()<end){if(await evaluate(expression))return;await delay(200);}
    throw Error('UI wait timeout: '+expression);
  }
  await waitFor(`document.body?.innerText.includes('Synthetic Meridian corpus') && !!document.querySelector('input[type="text"]')`);
  const scenarios=[
    ['english','What is the Atlas standard return window, and when does its refund arrive?'],
    ['french','Quel est le numérateur du taux de clic de campagne ?'],
    ['unsupported','What is the personal email address of the Atlas returns manager?']
  ];
  const receipts=[];
  for(const [name,question] of scenarios) {
    await evaluate(`document.querySelector('input[type="text"]').focus()`);
    await page.call('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
    await page.call('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
    await page.call('Input.insertText',{text:question});
    await page.call('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',windowsVirtualKeyCode:9});
    await page.call('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',windowsVirtualKeyCode:9});
    await waitFor(`Array.from(document.querySelectorAll('button')).some(b=>b.innerText==='Ask'&&!b.disabled)`);
    await evaluate(`Array.from(document.querySelectorAll('button')).find(b=>b.innerText==='Ask').click()`);
    await waitFor(`document.querySelector('.st-key-answer')?.innerText.includes(${JSON.stringify(question)})`);
    await delay(500);
    const text=await evaluate(`document.querySelector('.st-key-answer').innerText`);
    if(!text.includes('coursenotes-qwen')||!text.includes('Inspect retrieved source passages'))throw Error('Missing model or source UI.');
    if((text.match(/meridian\.pdf — page \d+/g)||[]).length!==3)throw Error('Expected the fixed demo top-k=3.');
    if(name==='unsupported'&&!text.includes('I cannot find support'))throw Error('Unsupported demonstration did not abstain.');
    if(name!=='unsupported'&&(!text.includes('[meridian.pdf, p.')||text.includes('Answer withheld')))throw Error('No accepted cited answer in demo.');
    // Capture the actual rendered app; no image edits or synthesized interface.
    const metrics=await page.call('Page.getLayoutMetrics');
    const height=Math.ceil(metrics.cssContentSize.height);
    const shot=await page.call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
      clip:{x:0,y:0,width:1440,height,scale:1}});
    fs.writeFileSync(path.join(output,`${name}.png`),Buffer.from(shot.data,'base64'));
    receipts.push({scenario:name,question,rendered_answer_and_sources:text,screenshot:`docs/demo/${name}.png`});
    console.log('Verified and captured:',name);
  }
  fs.writeFileSync(path.join(output,'ui_receipt.json'),JSON.stringify({captured_utc:new Date().toISOString(),
    source:'Actual local Streamlit UI and live Qwen inference; development questions only.',
    top_k:3,indexed_chunks:33,browser:version.Browser,scenarios:receipts},null,2)+'\n');
  await page.call('Page.close');
} finally {
  if(browserConnection){try{await browserConnection.call('Browser.close');}catch{}browserConnection.close();}
  browser.kill();
}
