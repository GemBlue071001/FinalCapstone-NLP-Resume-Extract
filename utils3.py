from pydantic import BaseModel
from typing import List, Optional
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup

# Database configuration
DB_CONFIG = {
    "dbname": "my_database",
    "user": "my_user",
    "password": "my_password",
    "host": "18.136.123.243",
    "port": 5431
}

# Pydantic models - Define these BEFORE the VectorService class
class JobType(BaseModel):
    id: int
    name: str
    description: str

class JobPost(BaseModel):
    id: int
    jobTitle: str
    jobDescription: str
    salary: float
    postingDate: str
    expiryDate: str
    experienceRequired: int
    qualificationRequired: str
    benefits: str
    imageURL: str
    isActive: bool
    companyId: int
    companyName: str
    websiteCompanyURL: str
    jobType: JobType
    jobLocationCities: List[str]
    jobLocationAddressDetail: List[str]
    skillSets: List[str]

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    ids: List[int]

# Vector service class - Define AFTER the models
class VectorService:
    def __init__(self):
        print("Initializing sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    @staticmethod
    def clean_html(text: str) -> str:
        """Remove HTML tags from text"""
        if isinstance(text, str):
            return BeautifulSoup(text, "html.parser").get_text(separator=' ', strip=True)
        return ""

    def prepare_job_text(self, job: JobPost) -> str:
        """Prepare job text for embedding"""
        return f"""
        Title: {job.jobTitle}
        Company: {job.companyName}
        Description: {self.clean_html(job.jobDescription)}
        Requirements: {self.clean_html(job.qualificationRequired)}
        Benefits: {self.clean_html(job.benefits)}
        Job Type: {job.jobType.name}
        Experience Required: {job.experienceRequired} years
        Location: {', '.join(job.jobLocationCities) if job.jobLocationCities else 'Not specified'}
        Skills: {', '.join(job.skillSets) if job.skillSets else 'Not specified'}
        """

    def create_embedding(self, text: str) -> List[float]:
        """Create vector embedding as array of floats"""
        embedding = self.model.encode(text)
        return embedding.tolist()  # Convert numpy array to list of floats

    async def embed_job(self, job: JobPost) -> int:
        """Embed job and save to database"""
        try:
            # Create embedding
            job_text = self.prepare_job_text(job)
            vector = self.create_embedding(job_text)
            
            # Connect to database
            connection = psycopg2.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # Update database with real array
            sql_query = """
                UPDATE public."JobPosts"
                SET "VectorEmbedding" = %s
                WHERE "Id" = %s
                RETURNING "Id";
            """
            
            cursor.execute(sql_query, (vector, job.id))
            result = cursor.fetchone()
            connection.commit()
            
            return result[0] if result else None
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    async def search_jobs(self, query: str, limit: int = 5) -> List[int]:
        try:
            query_vector = self.create_embedding(query)
            connection = psycopg2.connect(**DB_CONFIG)
            cursor = connection.cursor()

            sql_query = """
            SELECT "Id",
                SQRT(SUM(POWER(t1.elem - t2.elem, 2))) as euclidean_distance
            FROM public."JobPosts" jp,
                UNNEST("VectorEmbedding") WITH ORDINALITY as t1(elem, ix),
                UNNEST(%s::real[]) WITH ORDINALITY as t2(elem, ix)
            WHERE t1.ix = t2.ix
            GROUP BY "Id"
            ORDER BY euclidean_distance ASC
            LIMIT %s;
            """
            
            cursor.execute(sql_query, (query_vector, limit))
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()