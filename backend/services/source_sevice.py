from models import Source, db

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