import streamlit as st
import os
from scraper import JournalScraper
from db_manager import DatabaseManager
from chat_manager import ChatManager
import time
import re
import PyPDF2

# Initialize session state variables
if 'download_status' not in st.session_state:
    st.session_state.download_status = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}

# Page configuration
st.set_page_config(
    page_title="Journal PDF Downloader",
    page_icon="📚",
    layout="wide"
)

# Ensure 'pdfs' directory exists
os.makedirs('pdfs', exist_ok=True)

# Initialize components
db = DatabaseManager('journal_downloads.db')
scraper = JournalScraper()
chat_manager = ChatManager()

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        st.error(f"Error extracting PDF text: {e}")
        return ""

def main():
    st.title("📚 Journal PDF Downloader")

    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Download PDFs", "Chat with PDFs", "Todos"])

    with tab1:
        st.markdown("""
        Enter the URL of the volume you want to download.
        Example: www.jofph.com/articles/38-1
        """)

        col1, col2 = st.columns([2, 1])

        with col1:
            url = st.text_input(
                "Volume URL:",
                placeholder="www.jofph.com/articles/38-1"
            )

            if url:
                try:
                    with st.spinner('Loading available articles...'):
                        articles = scraper.get_articles_from_url(url)

                    if articles:
                        st.subheader(f"Available Articles ({len(articles)})")

                        # Button to download all PDFs
                        if st.button("Download All PDFs"):
                            for article in articles:
                                try:
                                    with st.spinner(f'Downloading: {article["title"]}'):
                                        volume_dir = os.path.join('pdfs', f'volume_{article["volume"]}')
                                        os.makedirs(volume_dir, exist_ok=True)

                                        filename = f"vol_{article['volume']}_issue_{article['issue']}_{article['doi'].replace('/', '_') if article['doi'] else 'article'}.pdf"
                                        filepath = os.path.join(volume_dir, filename)

                                        if not os.path.exists(filepath):
                                            success = scraper.download_pdf(article['pdf_url'], filepath)
                                            if success:
                                                db.add_download(article['volume'], article['issue'], filepath)
                                                st.success(f"✅ Downloaded: {filename}")
                                            else:
                                                st.error(f"❌ Error downloading: {filename}")
                                        else:
                                            st.info(f"📄 Already exists: {filename}")
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        # List individual articles
                        for article in articles:
                            with st.container():
                                st.markdown(f"**{article['title']}**")
                                if article['doi']:
                                    st.markdown(f"DOI: {article['doi']}")

                                if st.button(f"Download PDF", key=f"btn_{article['doi'] or article['title']}"):
                                    try:
                                        with st.spinner('Downloading PDF...'):
                                            volume_dir = os.path.join('pdfs', f'volume_{article["volume"]}')
                                            os.makedirs(volume_dir, exist_ok=True)

                                            filename = f"vol_{article['volume']}_issue_{article['issue']}_{article['doi'].replace('/', '_') if article['doi'] else 'article'}.pdf"
                                            filepath = os.path.join(volume_dir, filename)

                                            if not os.path.exists(filepath):
                                                success = scraper.download_pdf(article['pdf_url'], filepath)
                                                if success:
                                                    db.add_download(article['volume'], article['issue'], filepath)
                                                    st.success(f"PDF downloaded successfully: {filename}")
                                                else:
                                                    st.error("Error downloading the PDF")
                                            else:
                                                st.info(f"File already exists: {filename}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                                st.markdown("---")
                    else:
                        st.warning("No articles found at this URL")

                except Exception as e:
                    st.error(f"Error loading articles: {e}")

        with col2:
            st.subheader("Statistics")
            stats = db.get_statistics()
            st.metric("Total Downloads", stats['total_downloads'])
            st.metric("Total Volumes", stats['total_volumes'])
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")

            st.subheader("Download History")
            history = db.get_download_history(5)
            for entry in history:
                st.text(f"Volume {entry[0]}, Issue {entry[1]} - {entry[2]}")

    with tab2:
        st.subheader("💬 Chat with PDFs")

        # List available PDFs
        pdf_files = []
        for root, dirs, files in os.walk('pdfs'):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))

        if not pdf_files:
            st.warning("No PDFs available. Please download some papers first.")
            return

        # Select PDF to chat about
        selected_pdf = st.selectbox(
            "Select a PDF to chat about:",
            pdf_files,
            format_func=lambda x: os.path.basename(x)
        )

        if selected_pdf:
            # Create columns for chat interface
            chat_col, history_col = st.columns([2, 1])

            with chat_col:
                # Chat interface
                user_message = st.text_area("Ask a question about the paper:", height=100)

                if st.button("Send"):
                    if not os.environ.get("OPENAI_API_KEY"):
                        st.error("Please set the OPENAI_API_KEY environment variable.")
                        return

                    with st.spinner("Processing your question..."):
                        # Extract text from PDF
                        pdf_text = extract_pdf_text(selected_pdf)
                        if pdf_text:
                            # Get response from ChatGPT
                            response = chat_manager.chat_with_pdf(pdf_text, user_message)
                            # Store in database
                            db.add_chat_history(selected_pdf, user_message, response)
                            # Show response
                            st.write("Response:", response)
                        else:
                            st.error("Could not extract text from the PDF.")

            with history_col:
                # Show chat history
                st.subheader("Chat History")
                history = db.get_chat_history(selected_pdf)
                for msg in history:
                    with st.expander(f"Q: {msg[0][:50]}..."):
                        st.write("Question:", msg[0])
                        st.write("Answer:", msg[1])
                        st.write("Time:", msg[2])

    with tab3:
        st.subheader("📝 Todo List")

        # Add new todo
        with st.form("add_todo"):
            title = st.text_input("Todo Title")
            description = st.text_area("Description")

            # Optional: Link to PDF
            pdf_files = []
            for root, dirs, files in os.walk('pdfs'):
                for file in files:
                    if file.endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))

            selected_pdf = st.selectbox(
                "Link to PDF (optional)",
                ["None"] + pdf_files,
                format_func=lambda x: os.path.basename(x) if x != "None" else "None"
            )

            if st.form_submit_button("Add Todo"):
                if title:
                    pdf_path = None if selected_pdf == "None" else selected_pdf
                    db.add_todo(title, description, pdf_path)
                    st.success("Todo added successfully!")
                else:
                    st.error("Please enter a title for the todo.")

        # Display todos
        st.subheader("Current Todos")

        # Filter todos
        status_filter = st.selectbox(
            "Filter by status:",
            ["All", "Pending", "In Progress", "Completed"]
        )

        status = None if status_filter == "All" else status_filter.lower()
        todos = db.get_todos(status)

        if not todos:
            st.info("No todos found.")
        else:
            for todo in todos:
                todo_id, title, desc, pdf_path, status, created_at, completed_at = todo

                with st.expander(f"{title} ({status})"):
                    st.write("Description:", desc if desc else "No description")
                    if pdf_path:
                        st.write("Linked PDF:", os.path.basename(pdf_path))
                    st.write("Created:", created_at)
                    if completed_at:
                        st.write("Completed:", completed_at)

                    # Status update buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Mark Pending", key=f"pending_{todo_id}"):
                            db.update_todo_status(todo_id, "pending")
                            st.rerun()
                    with col2:
                        if st.button("Mark In Progress", key=f"progress_{todo_id}"):
                            db.update_todo_status(todo_id, "in progress")
                            st.rerun()
                    with col3:
                        if st.button("Mark Completed", key=f"completed_{todo_id}"):
                            db.update_todo_status(todo_id, "completed")
                            st.rerun()

if __name__ == "__main__":
    main()