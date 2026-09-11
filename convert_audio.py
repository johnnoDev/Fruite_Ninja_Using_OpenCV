import os
from moviepy import AudioFileClip

def convert_audio():
    audio_dir = "assets/audio"
    if not os.path.exists(audio_dir):
        print("Audio directory not found.")
        return

    print("Scanning for .m4a files to convert...")
    
    for filename in os.listdir(audio_dir):
        if filename.lower().endswith(".m4a"):
            m4a_path = os.path.join(audio_dir, filename)
            wav_path = os.path.join(audio_dir, filename.rsplit(".", 1)[0] + ".wav")
            
            print(f"Converting: {filename} -> {os.path.basename(wav_path)}")
            
            try:
                clip = AudioFileClip(m4a_path)
                clip.write_audiofile(wav_path, logger=None)
                clip.close()
                
                # Verify passed
                if os.path.exists(wav_path):
                    print(f"Success. Removing original {filename}")
                    os.remove(m4a_path)
                else:
                    print(f"Error: wav file not created for {filename}")
                    
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    convert_audio()
