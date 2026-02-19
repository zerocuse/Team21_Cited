from app import db

class User(db.Model):
    __tablename__ = 'users'

    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    membership_status = db.Column(db.String(20), nullable=False, default='free') # can be free, premium, admin
    creation_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)

    def __repr__(self): # will be used for debugging
        return (f"<User {self.username} ({self.email}) - Membership: {self.membership_status}>")
    
class Claim(db.Model):
    __tablename__ = 'claims'

    claimID = db.Column(db.Integer, primary_key=True)
    claim_text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=True) # e.g. true, false, partially true
    queried_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    view_count = db.Column(db.Integer, default=0)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)

    def __repr__(self):
        return f"<Claim {self.claim_text[:50]}... - Status: {self.status}>"
    

class FactCheck(db.Model):
    __tablename__ = 'fact_checks'

    factCheckID = db.Column(db.Integer, primary_key=True)
    verdict = db.Column(db.String(20), nullable=False) # e.g. true, false, partially true
    confidence_score = db.Column(db.Float, nullable=True) # 0-100 confidence score
    explanation = db.Column(db.Text, nullable=True) # detailed explanation of the verdict
    ai_reasoning = db.Column(db.Text, nullable=True) # AI's reasoning process
    checked_via = db.Column(db.String(50), nullable=True) # e.g. LLM, human expert, hybrid, existing fact
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    claimID = db.Column(db.Integer, db.ForeignKey('claims.claimID'), nullable=False)

    def __repr__(self):
        return f"<FactCheck for ClaimID {self.claimID} - Verdict: {self.verdict}>"

class Source(db.Model):
    __tablename__ = 'sources'

    sourceID = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    source_credibility_rating = db.Column(db.Float, nullable=True) # can be null
    source_type = db.Column(db.String(50), nullable=False) # e.g. news, academic, social media
    publication_date = db.Column(db.DateTime, nullable=True) # can be null

    def __repr__(self):
        return f"<Source {self.title} ({self.url}) - Type: {self.source_type}>"
    
class Citation(db.Model):
    __tablename__ = 'citations'

    info_used = db.Column(db.Text, nullable=True) # optional quote from the source that supports/refutes the claim
    citationID = db.Column(db.Integer, primary_key=True)
    claimID = db.Column(db.Integer, db.ForeignKey('claims.claimID'), nullable=False)
    sourceID = db.Column(db.Integer, db.ForeignKey('sources.sourceID'), nullable=False)

    def __repr__(self):
        return f"<Citation ClaimID {self.claimID} - SourceID {self.sourceID} - Relevance: {self.relevance_score}>"
    
class Tag(db.Model):
    __tablename__ = 'tag'

    tagID = db.Column(db.Integer, primary_key=True)
    tagName = db.Column(db.String(50), unique=True, nullable=False)
    tagCategory = db.Column(db.String(50), nullable=False) # e.g. politics, health, science
    timesUsed = db.Column(db.Integer, default=0) # how many times this tag has been used in reports

    def __repr__(self):
        return f"<Tag {self.tagName}>"
    
class ClaimTagLink(db.Model):
    __tablename__ = 'claim_tag_link'

    claimID = db.Column(db.Integer, db.ForeignKey('claims.claimID'), primary_key=True)
    tagID = db.Column(db.Integer, db.ForeignKey('tag.tagID'), primary_key=True)

    def __repr__(self):
        return f"<ClaimTagLink ClaimID {self.claimID} - TagID {self.tagID}>"
    
class ClaimSourceLink(db.Model):
    __tablename__ = 'claim_source_link'

    claimID = db.Column(db.Integer, db.ForeignKey('claims.claimID'), primary_key=True)
    sourceID = db.Column(db.Integer, db.ForeignKey('sources.sourceID'), primary_key=True)

    def __repr__(self):
        return f"<ClaimSourceLink ClaimID {self.claimID} - SourceID {self.sourceID}>"
    
class SourceKnowledgeLink(db.Model):
    __tablename__ = 'source_knowledge_link'

    sourceID = db.Column(db.Integer, db.ForeignKey('sources.sourceID'), primary_key=True)
    factID = db.Column(db.Integer, db.ForeignKey('knowledge_base.factID'), primary_key=True)

    def __repr__(self):
        return f"<SourceKnowledgeLink SourceID {self.sourceID} - FactID {self.factID}>"
    
class KnowledgeBaseEntry(db.Model):
    __tablename__ = 'knowledge_base'

    factID = db.Column(db.Integer, primary_key=True)
    umbrellaTopic = db.Column(db.String(100), nullable=False) # e.g. COVID-19, Climate Change
    content = db.Column(db.Text, nullable=False) # the fact-checked content
    summary = db.Column(db.Text, nullable=True) # optional summary of the content
    dateVerified = db.Column(db.DateTime, default=db.func.current_timestamp())
    verificationStatus = db.Column(db.String(20), nullable=False) # e.g. true, false, partially true
    confidenceScore = db.Column(db.Float, nullable=True) # 0-100 confidence score

    def __repr__(self):
        return f"<KnowledgeBaseEntry {self.claim[:50]}... - Verdict: {self.verdict}>"


    