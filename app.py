import streamlit as st
import os
import subprocess
from PIL import Image
import time
from main import *

def main():

    st.header(':musical_keyboard: Perfect THAT Tune!', divider='rainbow')
    st.caption('The website provides a simple evaluation on piano performance. Users can upload digital music sheets '
               '**AND** recordings of their piano performances for assessment. The service converts user-uploaded '
               'files into piano roll images, followed by utilizing image processing to improve their quality. It '
               'then identifies incorrectly played notes within the recording.')
    st.subheader('Evaluation Preferences:')
    # Checkbox for selecting mode
    mode = st.checkbox("Include Timing (for better accuracy)", value=True)

    # File upload for image
    uploaded_image = st.file_uploader("Upload your image here", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        st.success("Music Sheet uploaded successfully.")

    # File upload for audio
    uploaded_audio = st.file_uploader("Upload your piano recording here (.mp3, .ogg, .wav, .flac, .m4a)", type=["mp3", "ogg", "wav", "flac", "m4a"])
    if uploaded_audio is not None:
        st.success("Recording uploaded successfully.")

    if uploaded_image and uploaded_audio is not None:
        # Save the uploaded image as "input_sheet"
        input_sheet_path = "input_sheet.png"
        with open(input_sheet_path, "wb") as f:
            f.write(uploaded_image.getbuffer())

        # Display uploaded image
        if st.button('Evaluate'):
            try:
                # Ensure the "temp" directory exists
                os.makedirs("temp", exist_ok=True)

                # Save the uploaded image temporarily
                with open(os.path.join("temp", uploaded_image.name), "wb") as f:
                    f.write(uploaded_image.getbuffer())

                # Save the uploaded audio temporarily
                with open(os.path.join("temp", uploaded_audio.name), "wb") as f:
                    f.write(uploaded_audio.getbuffer())

                # Determine mode based on checkbox state
                mode_arg = "1" if mode else "2"

                # Run the command with the uploaded image and audio paths, and mode as arguments
                cmd = f"python main.py ./temp/{uploaded_image.name} --mode {mode_arg} ./temp/{uploaded_audio.name}"
                st.info(f"Evaluating your piano performance...It might take a few minutes...")

                # Execute the command and wait for it to finish
                subprocess.run(cmd, shell=True, check=True)

                # Clear the evaluation message
                st.empty()
                st.success("Evaluation finished!")
                # Load and display result image
                result_path = "result.png"  # Change this to the path of your result image
                result_image = Image.open(result_path)
                st.image(result_image, caption='Result Image', use_column_width=True)

                # Load and display overlay image
                overlay_path = "overlay.png"  # Change this to the path of your overlay image
                overlay_image = Image.open(overlay_path)
                st.image(overlay_image, caption='Overlay Image', use_column_width=True)

            except Exception as e:
                st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
