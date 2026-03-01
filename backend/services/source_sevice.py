from models import Source, Citation, ClaimSourceLink, SourceKnowledgeLink, Claim, db

def create_source(source_name: str, source_url: str) -> Source:
    if not source_name or not source_name.strip():
        raise ValueError("Source name cannot be null or empty")
    if not source_url or not source_url.strip():
        raise ValueError("Source URL cannot be null or empty")
    
    new_source = Source(
        title=source_name,
        url=source_url,
        source_type="unknown" # default type, can be updated later
    )
    
    db.session.add(new_source)
    db.session.commit()
    return new_source

def link_source_to_claim(sourceID: int, claimID: int) -> None:
    source = Source.query.get(sourceID)
    if not source:
        raise ValueError(f"Source with ID {sourceID} does not exist")
    
    claim = Claim.query.get(claimID)
    if not claim:
        raise ValueError(f"Claim with ID {claimID} does not exist")
    
    claim.sources.append(source)
    db.session.commit()

def add_citation(claimID: int, sourceID: int, info_used: str = None) -> Citation:
    source = Source.query.get(sourceID)
    if not source:
        raise ValueError(f"Source with ID {sourceID} does not exist")
    
    claim = Claim.query.get(claimID)
    if not claim:
        raise ValueError(f"Claim with ID {claimID} does not exist")
    
    new_citation = Citation(
        claimID=claimID,
        sourceID=sourceID,
        info_used=info_used
    )
    
    db.session.add(new_citation)
    db.session.commit()
    return new_citation

def get_sources_for_claim(claimID: int) -> list[Source]:
    claim = Claim.query.get(claimID)
    if not claim:
        raise ValueError(f"Claim with ID {claimID} does not exist")
    
    return claim.sources

def search_sources_by_keyword(keyword: str) -> list[Source]:
    if not keyword or not keyword.strip():
        raise ValueError("Keyword cannot be null or empty")
    
    keyword_pattern = f"%{keyword}%"
    sources = Source.query.filter(
        db.or_(
            Source.title.ilike(keyword_pattern),
            Source.url.ilike(keyword_pattern)
        )
    ).all()
    
    return sources

