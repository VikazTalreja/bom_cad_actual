# step_parser.py - COMPLETE REPLACEMENT
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def parse_step_file(file_path: str) -> List[Dict]:
    """Robust STEP file parser for cloud environments"""
    try:
        # Read with multiple encoding attempts
        content = None
        encodings = ['utf-8', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # Fallback: binary read with replacement
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
        
        # Normalize line endings and remove BOM if present
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        content = content.lstrip('\ufeff')
        
        entities = []
        
        # Multiple parsing strategies
        patterns = [
            r'#(\d+)\s*=\s*([^;]*);',  # Standard format
            r'(\#\d+\s*=\s*[^;]*;)',   # Alternative format
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
            for match in matches:
                if pattern == r'#(\d+)\s*=\s*([^;]*);':
                    entity_id, entity_def = match.groups()
                else:
                    full_match = match.group(1)
                    entity_id_match = re.search(r'#(\d+)', full_match)
                    if entity_id_match:
                        entity_id = entity_id_match.group(1)
                        entity_def = full_match.replace(f"#{entity_id} =", "").strip(' ;')
                    else:
                        continue
                
                entity = _parse_entity(entity_id.strip(), entity_def.strip())
                if entity:
                    entities.append(entity)
            
            if entities:  # Stop if we found entities
                break
        
        logger.info(f"Parsed {len(entities)} entities from STEP file")
        return entities
        
    except Exception as e:
        logger.error(f"Error parsing STEP file {file_path}: {e}")
        return []

def _parse_entity(entity_id: str, entity_def: str) -> Dict:
    """Parse individual STEP entity with robust error handling"""
    try:
        if not entity_def:
            return None
            
        # Extract entity type (first word)
        type_match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)', entity_def)
        if not type_match:
            return None
            
        entity_type = type_match.group(1).upper()
        
        # Extract parameters
        parameters = []
        param_match = re.search(r'\((.*)\)', entity_def, re.DOTALL)
        
        if param_match:
            param_str = param_match.group(1)
            parameters = _parse_parameters(param_str)
        
        return {
            'id': entity_id,
            'type': entity_type,
            'parameters': parameters,
            'raw': f"#{entity_id} = {entity_def};"
        }
        
    except Exception as e:
        logger.warning(f"Error parsing entity #{entity_id}: {e}")
        return None

def _parse_parameters(param_str: str) -> list:
    """Simple parameter parsing that works reliably"""
    if not param_str.strip():
        return []
    
    try:
        # Split on commas outside of quotes and nested structures
        params = []
        current = ""
        depth = 0
        in_quotes = False
        
        for char in param_str:
            if char == "'" and not in_quotes:
                in_quotes = True
            elif char == "'" and in_quotes:
                in_quotes = False
                
            if not in_quotes:
                if char in '([':
                    depth += 1
                elif char in ')]':
                    depth -= 1
                elif char == ',' and depth == 0:
                    params.append(current.strip())
                    current = ""
                    continue
                    
            current += char
        
        if current.strip():
            params.append(current.strip())
            
        return [_clean_param(p) for p in params]
        
    except Exception:
        # Fallback: simple split
        return [p.strip() for p in param_str.split(',')]

def _clean_param(param: str):
    """Clean parameter value"""
    param = param.strip()
    
    # Remove quotes
    if (param.startswith("'") and param.endswith("'")) or (param.startswith('"') and param.endswith('"')):
        return param[1:-1]
    
    # Handle references
    if param.startswith("#"):
        return f"REF:{param[1:].strip()}"
    
    # Handle boolean values
    if param.upper() in ['.T.', 'TRUE', 'T']:
        return True
    if param.upper() in ['.F.', 'FALSE', 'F']:
        return False
    
    # Handle numbers
    try:
        if '.' in param:
            return float(param)
        else:
            return int(param)
    except (ValueError, TypeError):
        pass
    
    return param

def extract_step_components(step_data: List[Dict]) -> List[Dict]:
    """Extract components with better cloud compatibility"""
    components = []
    
    # Look for common patterns in STEP files
    for entity in step_data:
        comp_data = _extract_from_entity(entity)
        if comp_data:
            components.append(comp_data)
    
    # If no components found, create basic ones from entities with data
    if not components:
        for entity in step_data[:50]:  # Limit to first 50 to avoid overload
            comp_data = _create_basic_component(entity)
            if comp_data:
                components.append(comp_data)
    
    logger.info(f"Extracted {len(components)} components")
    return components

def _extract_from_entity(entity: Dict) -> Dict:
    """Extract component data from entity"""
    part_number = ""
    description = ""
    
    # Scan parameters for meaningful data
    for param in entity['parameters']:
        if isinstance(param, str) and param and not param.startswith('REF:'):
            # Check if it looks like a part number
            if _looks_like_part_number(param):
                part_number = param
            # Check if it looks like a description
            elif _looks_like_description(param):
                description = param
    
    if part_number or description:
        return {
            'id': entity['id'],
            'type': entity['type'],
            'part_number': part_number,
            'description': description
        }
    
    return None

def _create_basic_component(entity: Dict) -> Dict:
    """Create basic component from any entity with data"""
    for param in entity['parameters']:
        if isinstance(param, str) and len(param) > 3 and not param.startswith('REF:'):
            return {
                'id': entity['id'],
                'type': entity['type'],
                'part_number': param[:50],  # Truncate if too long
                'description': f"{entity['type']} component",
                'footprint': '',  # Add default empty footprint
                'context': ''     # Add default empty context
            }
    
    return None

def _looks_like_part_number(text: str) -> bool:
    """Heuristic to identify part numbers"""
    if not text or len(text) < 4:
        return False
    
    # Common part number patterns
    patterns = [
        r'^[A-Z0-9\-_/.]+$',  # Alphanumeric with symbols
        r'^[0-9\-]+[A-Z]?$',   # Numbers with dashes and optional letter
        r'^[A-Z]{2,}\d+',      # Letters followed by numbers
    ]
    
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    
    return False

def _looks_like_description(text: str) -> bool:
    """Heuristic to identify descriptions"""
    if not text or len(text) < 10:
        return False
    
    # Should contain spaces and meaningful words
    if ' ' in text and sum(1 for c in text if c.isalpha()) > 5:
        return True
    
    return False
