import streamlit as st
import os
import subprocess
from PIL import Image
import time
from main import *

def main():

    st.header(':musical_keyboard: Perfect THAT Tune!', divider='rainbow')
    st.caption('The website provides a simple evaluation on piano performance. Users can upload digital music sheets **AND** recordings of their piano performances for assessment. ')
    st.markdown(
        """
        Evaluation is limited to:
        - Monophonic
        - Treble Clef
        
        Sample inputs can be found from the links below:
        
        [Music Sheets](https://drive.google.com/drive/folders/1mQlrfI-o_LHIb02TYykAhbftHWzNNC7S?usp=sharing)
       
        [Piano Performance](https://drive.google.com/drive/folders/1Xfw3plX6OCqm9ZLwHqGPf8LcLbh0gSr3?usp=sharing)
        
        :exclamation: _NOTE: It's recommended to evaluate note recognition by bar, as attempting to recognize every 
        note on the entire music sheet might not capture each individual bar accurately._"""
    )

    st.subheader('Evaluation Preferences:')
    # Checkbox for selecting mode
    mode = st.checkbox("Include Timing (for better accuracy)", value=True)

    # File upload for image
    uploaded_image = st.file_uploader("Upload your music sheet here", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        st.success("Music Sheet uploaded successfully.")

    # File upload for audio
    uploaded_audio = st.file_uploader("Upload your piano recording here (.mp3, .wav, .flac)", type=["mp3", "wav", "flac"])
    if uploaded_audio is not None:
        st.success("Recording uploaded successfully.")

    if uploaded_image and uploaded_audio is not None:
        # Determine file extensions
        image_extension = uploaded_image.name.split(".")[-1]
        audio_extension = uploaded_audio.name.split(".")[-1]

        # Display uploaded image
        if st.button('Evaluate'):
            try:
                # Ensure the "temp" directory exists
                os.makedirs("temp", exist_ok=True)

                # Save the uploaded image temporarily
                with open(os.path.join("temp", f"input_sheet.{image_extension}"), "wb") as f:
                    f.write(uploaded_image.getbuffer())

                # Save the uploaded audio temporarily
                with open(os.path.join("temp", f"input_recording.{audio_extension}"), "wb") as f:
                    f.write(uploaded_audio.getbuffer())

                # Determine mode based on checkbox state
                mode_arg = "1" if mode else "2"

                # Get the path to the Python binary in the virtual environment
                python_binary = sys.executable
                print(uploaded_image.name)
                # Run the command with the uploaded image and audio paths, and mode as arguments
                cmd = [python_binary, "main.py", f"./temp/input_sheet.{image_extension}", "--mode", mode_arg,
                       f"./temp/input_recording.{audio_extension}"]
                # cmd = f"python main.py ./temp/{uploaded_image.name} --mode {mode_arg} ./temp/{uploaded_audio.name}"
                st.info(f"Evaluating your piano performance...It might take a few minutes...")

                # Execute the command and wait for it to finish
                subprocess.run(cmd, check=True)

                st.success("Evaluation finished!")
                # Load and display result image
                result_path = "result.png"
                result_image = Image.open(result_path)
                st.image(result_image, caption='Result Image', use_column_width=True)

                # Load and display overlay image
                overlay_path = "overlay.png"
                overlay_image = Image.open(overlay_path)
                st.image(overlay_image, caption='Overlay Image', use_column_width=True)


            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    st.warning("No music notes detected in this music sheet, please choose another file.")
                elif e.returncode == 2:
                    st.error("Piano recording recognition failed, please choose another file.")
                elif e.returncode == 3:
                    st.error("Error opening the audio file, please choose another file.")
                else:
                    st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
