# app.py - REPLACE the STEP file processing section
import tempfile
import os

# MODIFY the STEP processing part:
with st.spinner("Processing files..."):
    try:
        # Process BOM
        bom_df = parse_bom_pdf(bom_file)
        bom_df = clean_bom_data(bom_df)
        
        # Save STEP file with proper temp file handling for cloud
        with tempfile.NamedTemporaryFile(delete=False, suffix='.step', mode='w+b') as tmp_step:
            # Write bytes for compatibility
            if hasattr(step_file, 'getvalue'):
                tmp_step.write(step_file.getvalue())
            else:
                tmp_step.write(step_file.read())
            step_path = tmp_step.name
        
        # Ensure file is closed before reading
        tmp_step.close()
        
        # Process STEP with explicit file handling
        step_data = parse_step_file(step_path)
        step_components = extract_step_components(step_data)
        
        # Match components
        match_results = match_components(bom_df, step_components)
        
        # Display results
        st.subheader("Matching Results")
        st.dataframe(match_results)
        
        # Clean up temp file immediately
        try:
            os.unlink(step_path)
        except:
            pass
            
    except Exception as e:
        st.error(f"Processing error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# app.py - ADD debug information display
# After the matching results, add:

if debug_mode:
    st.subheader("Debug Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("BOM Data Sample:")
        st.dataframe(bom_df.head(10))
        
        st.write(f"BOM rows: {len(bom_df)}")
    
    with col2:
        st.write("STEP Components Sample:")
        if step_components:
            step_df = pd.DataFrame(step_components)
            st.dataframe(step_df.head(10))
            st.write(f"STEP components: {len(step_components)}")
        else:
            st.write("No components extracted")
            
        st.write(f"STEP entities parsed: {len(step_data)}")
