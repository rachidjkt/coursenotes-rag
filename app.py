from pathlib import Path
import streamlit as st
from core import ROOT, Assistant, index_pdfs, documents_directory
st.set_page_config(page_title='CourseNotes RAG Assistant')
st.title('CourseNotes RAG Assistant')
st.caption('Local English/French PDF answers with inspectable page citations.')
uploads=st.file_uploader('Add course PDFs',type=['pdf'],accept_multiple_files=True)
if st.button('Save and index PDFs'):
    try:
        directory=documents_directory(); directory.mkdir(parents=True,exist_ok=True)
        for upload in uploads:
            name=Path(upload.name).name
            destination=directory/name
            if destination.exists() and destination.read_bytes()!=upload.getvalue():
                raise ValueError(f'{name} already exists with different content. Rename the upload to preserve the original.')
            destination.write_bytes(upload.getvalue())
        with st.spinner('Indexing locally…'): result=index_pdfs()
        st.success(result['status'])
        for warning in result['warnings']: st.warning(warning)
        st.session_state.pop('assistant',None)
        st.session_state.pop('result',None)
    except Exception as e: st.error(str(e))
question=st.text_input('Ask a question / Posez une question')
if st.button('Ask',disabled=not question.strip()):
    try:
        with st.spinner('Retrieving and answering locally…'):
            if 'assistant' not in st.session_state: st.session_state.assistant=Assistant()
            st.session_state.result=st.session_state.assistant.ask(question)
    except Exception as e: st.error(str(e))
if 'result' in st.session_state:
    result=st.session_state.result
    st.write(result['answer'])
    st.caption(f"{result['seconds']:.2f}s · {result['model']} · query rewritten: {result['rewritten']}")
    with st.expander('Inspect retrieved source passages',expanded=True):
        for p in result['passages']:
            st.markdown(f"**{p['filename']} — page {p['page']}**"); st.text(p['text'])
