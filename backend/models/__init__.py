from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

from models.models import User, Claim, FactCheck, Source, Citation, Tag, ClaimTagLink, ClaimSourceLink, KnowledgeBaseEntry
