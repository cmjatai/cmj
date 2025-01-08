import unittest
from unittest.mock import patch, MagicMock
import os

from st_app_ollama import (
    GeminiEmbeddingFunction, load_pdf, split_text, create_chroma_db,
    load_chroma_collection, get_relevant_passage, make_rag_prompt, generate_answer
)

class TestGeminiEmbeddingFunction(unittest.TestCase):
    @patch('st_app.genai.embed_content')
    def test_call(self, mock_embed_content):
        mock_embed_content.return_value = {"embedding": [0.1, 0.2, 0.3]}
        gemini_func = GeminiEmbeddingFunction()
        documents = ["doc1", "doc2"]
        embeddings = gemini_func(documents)
        self.assertEqual(embeddings, [0.1, 0.2, 0.3])
        mock_embed_content.assert_called_once()

class TestLoadPdf(unittest.TestCase):
    @patch('st_app.PdfReader')
    def test_load_pdf(self, mock_pdf_reader):
        mock_reader_instance = mock_pdf_reader.return_value
        mock_reader_instance.pages = [MagicMock(extract_text=lambda: "Page 1 text"), MagicMock(extract_text=lambda: "Page 2 text")]
        text = load_pdf("dummy_path.pdf")
        self.assertEqual(text, "Page 1 textPage 2 text")

class TestSplitText(unittest.TestCase):
    def test_split_text(self):
        text = "This is a sample text to be split into chunks."
        chunks = split_text(text, chunk_size=10, chunk_overlap=2)
        expected_chunks = ["This is a ", "sample text ", "to be split ", "into chunks."]
        self.assertEqual(chunks, expected_chunks)

class TestCreateChromaDb(unittest.TestCase):
    @patch('st_app.chromadb.PersistentClient')
    def test_create_chroma_db(self, mock_persistent_client):
        mock_client_instance = mock_persistent_client.return_value
        mock_collection = mock_client_instance.create_collection.return_value
        documents = ["doc1", "doc2"]
        db, name = create_chroma_db(documents, "dummy_path", "dummy_name")
        self.assertEqual(db, mock_collection)
        self.assertEqual(name, "dummy_name")
        mock_collection.add.assert_called()

class TestLoadChromaCollection(unittest.TestCase):
    @patch('st_app.chromadb.PersistentClient')
    def test_load_chroma_collection(self, mock_persistent_client):
        mock_client_instance = mock_persistent_client.return_value
        mock_collection = mock_client_instance.get_collection.return_value
        db = load_chroma_collection("dummy_path", "dummy_name")
        self.assertEqual(db, mock_collection)

class TestGetRelevantPassage(unittest.TestCase):
    @patch('st_app.chromadb.Collection.query')
    def test_get_relevant_passage(self, mock_query):
        mock_query.return_value = {'documents': [["Relevant passage"]]}
        db = MagicMock()
        passage = get_relevant_passage("query", db, 1)
        self.assertEqual(passage, "Relevant passage")

class TestMakeRagPrompt(unittest.TestCase):
    def test_make_rag_prompt(self):
        query = "What is AI?"
        relevant_passage = "AI stands for Artificial Intelligence."
        prompt = make_rag_prompt(query, relevant_passage)
        self.assertIn(query, prompt)
        self.assertIn(relevant_passage.replace("'", "").replace('"', "").replace("\n", " "), prompt)

class TestGenerateAnswer(unittest.TestCase):
    @patch('st_app.genai.GenerativeModel.generate_content')
    @patch('st_app.get_relevant_passage')
    @patch('st_app.make_rag_prompt')
    def test_generate_answer(self, mock_make_rag_prompt, mock_get_relevant_passage, mock_generate_content):
        mock_get_relevant_passage.return_value = "Relevant passage"
        mock_make_rag_prompt.return_value = "Prompt"
        mock_generate_content.return_value = MagicMock(text="Generated answer")
        db = MagicMock()
        query = "What is AI?"
        answer = generate_answer(db, query)
        self.assertEqual(answer, "Generated answer")

if __name__ == '__main__':
    unittest.main()