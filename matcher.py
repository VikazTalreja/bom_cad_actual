from fuzzywuzzy import fuzz
import pandas as pd
from typing import List, Dict
import re

def match_components(bom_df: pd.DataFrame, step_components: List[Dict]) -> pd.DataFrame:
    """Enhanced matching with fuzzy logic and better scoring"""
    # Pre-process BOM data
    bom_df = _preprocess_bom(bom_df)
    
    # Pre-process STEP components
    step_data = _preprocess_step(step_components)
    
    matches = []
    
    for _, bom_row in bom_df.iterrows():
        best_match = None
        best_score = 0.0  # Initialize with default value
        
        for step_comp in step_data:
            # Multi-criteria matching
            score = _calculate_enhanced_score(bom_row, step_comp)
            
            if score > best_score:
                best_score = score
                best_match = step_comp
        
        # Ensure best_score is always a valid number
        if best_match is None:
            best_score = 0.0
        
        matches.append({
            'BOM_PartNumber': bom_row['PartNumber'],
            'BOM_Description': bom_row['Description'],
            'STEP_PartNumber': best_match['part_number'] if best_match else None,
            'STEP_Description': best_match['description'] if best_match else None,
            'Match_Score': float(best_score) if best_match else 0.0,
            'Match_Type': _get_match_type(best_score) if best_match and best_score is not None else 'No Match'
        })
    
    # Post-process results
    return _post_process_matches(pd.DataFrame(matches))

def _preprocess_bom(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize BOM data"""
    df = df.copy()
    
    # Ensure required columns exist
    if 'PartNumber' not in df.columns:
        df['PartNumber'] = ''
    if 'Description' not in df.columns:
        df['Description'] = ''
    
    # Clean data
    df['PartNumber'] = df['PartNumber'].astype(str).str.upper().str.strip()
    df['Description'] = df['Description'].astype(str).str.upper().str.strip()
    
    # Remove empty/invalid rows
    df = df[(df['PartNumber'] != '') | (df['Description'] != '')]
    
    return df

def _preprocess_step(components: List[Dict]) -> List[Dict]:
    """Clean and standardize STEP components"""
    processed = []
    for comp in components:
        clean_comp = comp.copy()
        clean_comp['part_number'] = str(comp.get('part_number', '')).upper().strip()
        clean_comp['description'] = str(comp.get('description', '')).upper().strip()
        processed.append(clean_comp)
    return processed

def _calculate_enhanced_score(bom_row, step_comp) -> float:
    """Advanced scoring using multiple matching strategies"""
    try:
        scores = []
        
        # 1. Exact part number match
        if bom_row['PartNumber'] and step_comp['part_number']:
            if bom_row['PartNumber'] == step_comp['part_number']:
                return 1.0  # Perfect match
        
        # 2. Fuzzy part number matching
        if bom_row['PartNumber'] and step_comp['part_number']:
            try:
                scores.append(fuzz.ratio(bom_row['PartNumber'], step_comp['part_number']) / 100)
            except:
                pass
        
        # 3. Description contains part number
        if bom_row['PartNumber'] and step_comp['description']:
            if bom_row['PartNumber'] in step_comp['description']:
                scores.append(0.8)
        
        # 4. Fuzzy description matching
        if bom_row['Description'] and step_comp['description']:
            try:
                scores.append(fuzz.partial_ratio(bom_row['Description'], step_comp['description']) / 100 * 0.7)
            except:
                pass
        
        # 5. Token set ratio for descriptions
        if bom_row['Description'] and step_comp['description']:
            try:
                scores.append(fuzz.token_set_ratio(bom_row['Description'], step_comp['description']) / 100 * 0.6)
            except:
                pass
        
        return max(scores) if scores else 0.0
    except Exception as e:
        print(f"Error calculating score: {e}")
        return 0.0

def _get_match_type(score: float) -> str:
    """Classify match quality"""
    try:
        if score is None:
            return 'No Match'
        score = float(score)
        if score >= 0.95:
            return 'Exact Match'
        elif score >= 0.8:
            return 'Strong Match'
        elif score >= 0.6:
            return 'Partial Match'
        return 'Weak/No Match'
    except (ValueError, TypeError):
        return 'No Match'

def _post_process_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up and filter results"""
    try:
        # Remove duplicate matches
        df = df.drop_duplicates(
            subset=['BOM_PartNumber', 'BOM_Description'],
            keep='first'  # Can be 'first', 'last' or False
        )
        
        # Ensure Match_Score column exists and has valid values
        if 'Match_Score' not in df.columns:
            df['Match_Score'] = 0.0
        
        # Convert Match_Score to numeric, handling any invalid values
        df['Match_Score'] = pd.to_numeric(df['Match_Score'], errors='coerce').fillna(0.0)
        
        # Sort by match score
        df = df.sort_values('Match_Score', ascending=False)
        
        # Format scores as percentages - with proper error handling
        def format_score(score):
            try:
                if pd.isna(score) or score is None:
                    return "0%"
                return f"{float(score):.0%}"
            except (ValueError, TypeError):
                return "0%"
        
        df['Match_Score'] = df['Match_Score'].apply(format_score)
        
        return df
    except Exception as e:
        print(f"Error in post-processing: {e}")
        # Return a basic version if processing fails
        return df