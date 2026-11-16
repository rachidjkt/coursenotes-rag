"""Synthetic fixtures only; never a course benchmark or generated ground-truth answer."""
import json
from core import ROOT, index_pdfs, PyPDFLoader
from evaluate import run
from reportlab.pdfgen import canvas

def prepare():
    root=ROOT/'smoke_data'; docs=root/'documents'; docs.mkdir(parents=True,exist_ok=True)
    pages=['Photosynthesis converts light energy into chemical energy in plants.',
           'La mitose produit deux cellules filles genetiquement identiques.']
    pdf=canvas.Canvas(str(docs/'synthetic.pdf'))
    for text in pages: pdf.drawString(45,750,text); pdf.showPage()
    pdf.save()
    extracted=PyPDFLoader(str(docs/'synthetic.pdf')).load()
    assert len(extracted)==2 and 'Photosynthesis' in extracted[0].page_content and 'mitose' in extracted[1].page_content
    result=index_pdfs(root); assert result.get('chunks',2)==2
    assert index_pdfs(root)['status']=='unchanged'
    blank=canvas.Canvas(str(docs/'blank.pdf')); blank.showPage(); blank.save()
    assert any('blank.pdf' in w for w in index_pdfs(root)['warnings'])
    rows=[{'id':'en','question':'What does photosynthesis convert?','answerable':True,'sources':[{'filename':'synthetic.pdf','page':1}],'verified':True},
          {'id':'fr','question':'Que produit la mitose ?','answerable':True,'sources':[{'filename':'synthetic.pdf','page':2}],'verified':True},
          {'id':'absent','question':'What is the course instructor email address?','answerable':False,'sources':[],'verified':True}]
    dataset=root/'questions.jsonl'; dataset.write_text('\n'.join(json.dumps(r) for r in rows),encoding='utf-8')
    print('PASS: PDF page extraction, unchanged-index reuse, scanned/blank warning',flush=True)
    return root,dataset

if __name__=='__main__':
    import sys
    root,dataset=prepare()
    if '--prepare-only' not in sys.argv:
        summary=run(dataset,root,k=2,output=ROOT/'results'/'smoke')
        raw=[json.loads(line) for line in (ROOT/'results'/'smoke'/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
        assert not raw[0]['output']['abstained'] and '[synthetic.pdf, p. 1]' in raw[0]['output']['answer']
        assert not raw[1]['output']['abstained'] and '[synthetic.pdf, p. 2]' in raw[1]['output']['answer']
        assert raw[2]['output']['abstained']
        print(json.dumps(summary,indent=2)); print('PASS: local end-to-end citations and abstention')
