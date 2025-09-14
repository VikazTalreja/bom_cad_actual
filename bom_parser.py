import pdfplumber
import pandas as pd
import re

def parse_bom_pdf(pdf_file) -> pd.DataFrame:
    """Improved PDF parser with better table detection"""
    with pdfplumber.open(pdf_file) as pdf:
        tables = []
        for page in pdf.pages:
            # Use text extraction for complex layouts
            text = page.extract_text()
            if text:
                # Custom parsing logic based on your BOM format
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                table = []
                for line in lines:
                    # Split on multiple spaces but preserve part numbers with spaces
                    cells = re.split(r'\s{2,}', line)
                    table.append(cells)
                if table:
                    tables.extend(table)
    
    # Convert to DataFrame
    if not tables:
        return pd.DataFrame(columns=['PartNumber', 'Description'])
    
    # Find the most common row length
    row_lengths = [len(row) for row in tables]
    common_length = max(set(row_lengths), key=row_lengths.count)
    
    # Standardize rows
    standardized = [row for row in tables if len(row) == common_length]
    
    # Create DataFrame
    if common_length >= 2:
        df = pd.DataFrame(standardized, columns=['PartNumber', 'Description'] + [f'Extra_{i}' for i in range(common_length-2)])
    else:
        df = pd.DataFrame(standardized, columns=['PartNumber'])
        df['Description'] = ''
    
    return df[['PartNumber', 'Description']]

def clean_bom_data(df: pd.DataFrame) -> pd.DataFrame:
    """Advanced BOM cleaning"""
    df = df.copy()
    
    # Clean part numbers
    df['PartNumber'] = df['PartNumber'].astype(str).apply(_clean_part_number)
    
    # Clean descriptions
    df['Description'] = df['Description'].astype(str).apply(_clean_description)
    
    # Remove empty rows
    df = df[(df['PartNumber'] != '') | (df['Description'] != '')]
    
    return df

def _clean_part_number(part_num: str) -> str:
    """Specialized part number cleaning"""
    part_num = part_num.upper().strip()
    # Remove common PDF artifacts
    part_num = re.sub(r'[^\w\-_/]', ' ', part_num)
    part_num = ' '.join(part_num.split())  # Collapse multiple spaces
    return part_num

def _clean_description(desc: str) -> str:
    """Specialized description cleaning"""
    desc = desc.upper().strip()
    # Remove line breaks and extra spaces
    desc = desc.replace('\n', ' ').replace('\r', ' ')
    desc = ' '.join(desc.split())
    return desc