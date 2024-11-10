import streamlit as st
import sqlite3
import requests
from xml.etree import ElementTree
import os
from datetime import datetime

# SQLite database path
db_path = r'C:\papers\research_papers.db'


#Insert papers data in DB
def insert_paper_data(paper_metadata):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT OR REPLACE INTO research_papers (paper_id, title, authors, abstract, journal, doi, submission_date, pdf_file_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        paper_metadata['paper_id'],
        paper_metadata['title'],
        paper_metadata['authors'],
        paper_metadata['abstract'],
        paper_metadata['journal'],
        paper_metadata['doi'],
        paper_metadata['submission_date'],
        paper_metadata['pdf_file_path']
    ))

    conn.commit()
    conn.close()

# Fet papers from Arxiv website
def fetch_arxiv(search_cond, paper_count, start_year):
    site_url = 'http://export.arxiv.org/api/query?'
#add search condition to url
    search_url = f"{site_url}search_query={search_cond}&start=0&max_results={paper_count}"

    # call arixiv api
    response = requests.get(search_url)
    
    if response.status_code != 200:
        st.error(f"Error fetching data from arXiv: {response.status_code}")
        return []

    # handle xml response
    root = ElementTree.fromstring(response.content)
    papers = []

    #get start date from year input
    start_date = datetime(start_year, 1, 1)

    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        # Extract publication date from the published tag
        pub_date_str = entry.find('{http://www.w3.org/2005/Atom}published').text.split('T')[0]
        pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')

        # Filter papers by publication date (>= Jan 1st of starting year)
        if pub_date >= start_date:
            paper_metadata = {
                'paper_id': entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1],  # Extract paper ID from the URL
                'title': entry.find('{http://www.w3.org/2005/Atom}title').text,
                'authors': ', '.join([author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')]),
                'abstract': entry.find('{http://www.w3.org/2005/Atom}summary').text,
                'journal': entry.find('{http://www.w3.org/2005/Atom}source').text if entry.find('{http://www.w3.org/2005/Atom}source') is not None else "N/A",
                'doi': entry.find('{http://arxiv.org/schemas/atom}doi').text if entry.find('{http://arxiv.org/schemas/atom}doi') is not None else None,
                'submission_date': pub_date_str,
                'pdf_file_path': ''
            }

            # Download the pdfs
            pdf_url = entry.find('{http://www.w3.org/2005/Atom}link').attrib['href'].replace('abs', 'pdf')
            pdf_filename = paper_metadata['paper_id'].replace('.', '_') + '.pdf'
            pdf_path = os.path.join(r'C:\papers', pdf_filename)

            # Save the pdf in folder
            pdf_response = requests.get(pdf_url)
            if pdf_response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_response.content)
                paper_metadata['pdf_file_path'] = pdf_path
            else:
                st.warning(f"Failed to download PDF for {paper_metadata['paper_id']}")

            # Insert the paper data into the database
            insert_paper_data(paper_metadata)

            # Add the paper to the list
            papers.append(paper_metadata)

    return papers

# Streamlit App
def main():
    # App title
    st.title("Find Relevant Papers")

    # Take user inputs for search condition, starting year, and number of papers
    search_cond = st.text_input("Search Keyword:", "")  
    paper_count = st.number_input("Number of Papers:", min_value=1, max_value=100)  
    start_year = st.number_input("Starting Year (YYYY):", min_value=2000, max_value=datetime.now().year, value=2019)  

    # Add a submit button
    if st.button("Submit"):
        if search_cond and paper_count and start_year:
            st.info(f"Fetching papers related to '{search_cond}' from {start_year} onwards...")

            # Fetch papers and display metadata. Users can now choose the papers they want and then do queried research on them with the other App
            papers = fetch_arxiv(search_cond, paper_count, start_year)

            if papers:
                st.success(f"{len(papers)} papers fetched successfully!")
                for paper in papers:
                    st.subheader(paper['title'])
                    st.write(f"*Paper ID*: {paper['paper_id']}")
                    st.write(f"*Authors*: {paper['authors']}")
                    st.write(f"*Abstract*: {paper['abstract']}")
                    st.write(f"*Journal*: {paper['journal']}")
                    st.write(f"*DOI*: {paper['doi']}")
                    st.write(f"*Submission Date*: {paper['submission_date']}")
                    st.write(f"*PDF File Path*: {paper['pdf_file_path']}")

            else:
                st.warning("No papers found or there was an issue fetching papers.")
        else:
            st.error("Please provide all inputs: search keyword, number of papers, and starting year.")

if __name__ == '__main__':
    main()
