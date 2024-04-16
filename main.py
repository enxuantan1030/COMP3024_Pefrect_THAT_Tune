import os
import sys
import subprocess

import audioread
import soundfile

from best_fit import fit
from rectangle import Rectangle
from note import Note
from random import randint
from midiutil import MIDIFile
from midi_to_img import *
from img_processing import *
from compare import *


staff_files = [
    "resources/template/staff2.png",
    "resources/template/staff.png"]
quarter_files = [
    "resources/template/quarter.png",
    "resources/template/solid-note.png"]
sharp_files = [
    "resources/template/sharp.png"]
flat_files = [
    "resources/template/flat-line.png",
    "resources/template/flat-space.png"]
half_files = [
    "resources/template/half-space.png",
    "resources/template/half-note-line.png",
    "resources/template/half-line.png",
    "resources/template/half-note-space.png"]
whole_files = [
    "resources/template/whole-space.png",
    "resources/template/whole-note-line.png",
    "resources/template/whole-line.png",
    "resources/template/whole-note-space.png"]

staff_imgs = [cv2.imread(staff_file, 0) for staff_file in staff_files]
quarter_imgs = [cv2.imread(quarter_file, 0) for quarter_file in quarter_files]
sharp_imgs = [cv2.imread(sharp_files, 0) for sharp_files in sharp_files]
flat_imgs = [cv2.imread(flat_file, 0) for flat_file in flat_files]
half_imgs = [cv2.imread(half_file, 0) for half_file in half_files]
whole_imgs = [cv2.imread(whole_file, 0) for whole_file in whole_files]

staff_lower, staff_upper, staff_thresh = 50, 150, 0.6
sharp_lower, sharp_upper, sharp_thresh = 50, 150, 0.70
flat_lower, flat_upper, flat_thresh = 50, 150, 0.77
quarter_lower, quarter_upper, quarter_thresh = 50, 150, 0.70
half_lower, half_upper, half_thresh = 50, 150, 0.70
whole_lower, whole_upper, whole_thresh = 50, 150, 0.70


def locate_images(img, templates, start, stop, threshold):
    locations, scale = fit(img, templates, start, stop, threshold)
    img_locations = []
    for i in range(len(templates)):
        w, h = templates[i].shape[::-1]
        w *= scale
        h *= scale
        img_locations.append([Rectangle(pt[0], pt[1], w, h) for pt in zip(*locations[i][::-1])])
    return img_locations


def merge_recs(recs, threshold):
    filtered_recs = []
    while len(recs) > 0:
        r = recs.pop(0)
        recs.sort(key=lambda rec: rec.distance(r))
        merged = True
        while(merged):
            merged = False
            i = 0
            for _ in range(len(recs)):
                if r.overlap(recs[i]) > threshold or recs[i].overlap(r) > threshold:
                    r = r.merge(recs.pop(i))
                    merged = True
                elif recs[i].distance(r) > r.w/2 + recs[i].w/2:
                    break
                else:
                    i += 1
        filtered_recs.append(r)
    return filtered_recs


if __name__ == "__main__":
    # Convert audio to midi
    # Check if audio file path argument is provided
    if len(sys.argv) > 4:
        audio_file_path = sys.argv[4]
        audio_name = os.path.splitext(os.path.basename(audio_file_path))[0]
        # Run basic-pitch library for audio
        audio_output_directory = f"output_audio"
        # Get the path to the Python binary in the virtual environment
        python_binary = sys.executable
        # Define the command and its arguments
        cmd = ["basic-pitch", audio_output_directory, audio_file_path]
        try:
            # Execute the command and wait for it to finish
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            sys.exit(2)  # Exit with status code 2 in case of an error
        except (soundfile.LibsndfileError, audioread.exceptions.NoBackendError) as e:
            print(f"Error opening the audio file: {e}")
            sys.exit(3)


    # Check if mode argument is provided
    if len(sys.argv) > 2 and sys.argv[2] == "--mode":
        mode = int(sys.argv[3])
    else:
        # Default mode to 1 if not provided
        mode = 1

    # 1. Specify input and output directories
    output_sheet_directory = "output_sheet"

    img_file = sys.argv[1]
    # 2. Specify input image file
    img_file = sys.argv[1:][0]
    img = cv2.imread(img_file, 0) # read
    img_gray = img
    img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    ret, img_gray = cv2.threshold(img_gray, 127, 255, cv2.THRESH_BINARY)
    img_width, img_height = img_gray.shape[::-1]

    # Check if the image width matches the specified values
    if img_width not in [2255, 1465]:
        staff_thresh = 0.77
    else:
        staff_thresh = 0.6

    print("Matching staff image...")
    staff_recs = locate_images(img_gray, staff_imgs, staff_lower, staff_upper, staff_thresh)

    print("Filtering weak staff matches...")
    staff_recs = [j for i in staff_recs for j in i]
    heights = [r.y for r in staff_recs] + [0]
    histo = [heights.count(i) for i in range(0, max(heights) + 1)]
    avg = np.mean(list(set(histo)))
    staff_recs = [r for r in staff_recs if histo[r.y] > avg]

    print("Merging staff image results...")
    staff_recs = merge_recs(staff_recs, 0.01)
    staff_recs_img = img.copy()
    for r in staff_recs:
        r.draw(staff_recs_img, (0, 0, 255), 2)
    cv2.imwrite('staff_recs_img.png', staff_recs_img)

    print("Discovering staff locations...")
    staff_boxes = merge_recs([Rectangle(0, r.y, img_width, r.h) for r in staff_recs], 0.01)
    staff_boxes_img = img.copy()
    for r in staff_boxes:
        r.draw(staff_boxes_img, (0, 0, 255), 2)
    cv2.imwrite('staff_boxes_img.png', staff_boxes_img)

    print("Matching sharp image...")
    sharp_recs = locate_images(img_gray, sharp_imgs, sharp_lower, sharp_upper, sharp_thresh)

    print("Merging sharp image results...")
    sharp_recs = merge_recs([j for i in sharp_recs for j in i], 0.5)
    sharp_recs_img = img.copy()
    for r in sharp_recs:
        r.draw(sharp_recs_img, (0, 0, 255), 2)
    cv2.imwrite('sharp_recs_img.png', sharp_recs_img)

    print("Matching flat image...")
    flat_recs = locate_images(img_gray, flat_imgs, flat_lower, flat_upper, flat_thresh)

    print("Merging flat image results...")
    flat_recs = merge_recs([j for i in flat_recs for j in i], 0.5)
    flat_recs_img = img.copy()
    for r in flat_recs:
        r.draw(flat_recs_img, (0, 0, 255), 2)
    cv2.imwrite('flat_recs_img.png', flat_recs_img)

    print("Matching quarter image...")
    quarter_recs = locate_images(img_gray, quarter_imgs, quarter_lower, quarter_upper, quarter_thresh)

    print("Merging quarter image results...")
    quarter_recs = merge_recs([j for i in quarter_recs for j in i], 0.5)
    quarter_recs_img = img.copy()
    for r in quarter_recs:
        r.draw(quarter_recs_img, (0, 0, 255), 2)
    cv2.imwrite('quarter_recs_img.png', quarter_recs_img)

    print("Matching half image...")
    half_recs = locate_images(img_gray, half_imgs, half_lower, half_upper, half_thresh)

    print("Merging half image results...")
    half_recs = merge_recs([j for i in half_recs for j in i], 0.5)
    half_recs_img = img.copy()
    for r in half_recs:
        r.draw(half_recs_img, (0, 0, 255), 2)
    cv2.imwrite('half_recs_img.png', half_recs_img)

    print("Matching whole image...")
    whole_recs = locate_images(img_gray, whole_imgs, whole_lower, whole_upper, whole_thresh)

    print("Merging whole image results...")
    whole_recs = merge_recs([j for i in whole_recs for j in i], 0.5)
    whole_recs_img = img.copy()
    for r in whole_recs:
        r.draw(whole_recs_img, (0, 0, 255), 2)
    cv2.imwrite('whole_recs_img.png', whole_recs_img)

    note_groups = []
    for box in staff_boxes:
        staff_sharps = [Note(r, "sharp", box)
                        for r in sharp_recs if abs(r.middle[1] - box.middle[1]) < box.h * 5.0 / 8.0]
        staff_flats = [Note(r, "flat", box)
                       for r in flat_recs if abs(r.middle[1] - box.middle[1]) < box.h * 5.0 / 8.0]
        quarter_notes = [Note(r, "4,8", box, staff_sharps, staff_flats)
                         for r in quarter_recs if abs(r.middle[1] - box.middle[1]) < box.h * 5.0 / 8.0]
        half_notes = [Note(r, "2", box, staff_sharps, staff_flats)
                      for r in half_recs if abs(r.middle[1] - box.middle[1]) < box.h * 5.0 / 8.0]
        whole_notes = [Note(r, "1", box, staff_sharps, staff_flats)
                       for r in whole_recs if abs(r.middle[1] - box.middle[1]) < box.h * 5.0 / 8.0]
        staff_notes = quarter_notes + half_notes + whole_notes
        staff_notes.sort(key=lambda n: n.rec.x)
        staffs = [r for r in staff_recs if r.overlap(box) > 0]
        staffs.sort(key=lambda r: r.x)
        note_color = (randint(0, 255), randint(0, 255), randint(0, 255))
        note_group = []
        i = 0;
        j = 0;
        while (i < len(staff_notes)):
            if (staff_notes[i].rec.x > staffs[j].x and j < len(staffs)):
                r = staffs[j]
                j += 1;
                if len(note_group) > 0:
                    note_groups.append(note_group)
                    note_group = []
                note_color = (randint(0, 255), randint(0, 255), randint(0, 255))
            else:
                note_group.append(staff_notes[i])
                staff_notes[i].rec.draw(img, note_color, 2)
                i += 1
        note_groups.append(note_group)

    for r in staff_boxes:
        r.draw(img, (0, 0, 255), 2)
    for r in sharp_recs:
        r.draw(img, (0, 0, 255), 2)
    flat_recs_img = img.copy()
    for r in flat_recs:
        r.draw(img, (0, 0, 255), 2)

    cv2.imwrite('res.png', img)

    for note_group in note_groups:
        print([note.note + " " + note.sym for note in note_group])

    # Create MIDI file for sheet
    sheet_midi = MIDIFile(1)

    track = 0
    time = 0
    channel = 0
    volume = 100

    sheet_midi.addTrackName(track, time, "Track")
    sheet_midi.addTempo(track, time, 140)

    for note_group in note_groups:
        duration = None
        for note in note_group:
            note_type = note.sym
            if note_type == "1":
                duration = 4
            elif note_type == "2":
                duration = 2
            elif note_type == "4,8":
                duration = 1 if len(note_group) == 1 else 0.5
            pitch = note.pitch
            sheet_midi.addNote(track, channel, pitch, time, duration, volume)
            time += duration

    if note_groups is None or len(note_groups) == 0:
        print('No music notes detected in this music sheet!')
        # Optionally, exit with a non-zero exit code
        sys.exit(1)
    else:
        sheet_midi.addNote(track, channel, pitch, time, 4, 0)

    # Extract the input image file name (without extension)
    img_file_path = sys.argv[1]
    img_file_name = os.path.splitext(os.path.basename(img_file_path))[0]

    # Save the sheet MIDI file
    sheet_output_path = f"{output_sheet_directory}/{img_file_name}_output_sheet.mid"
    with open(sheet_output_path, 'wb') as binfile:
        sheet_midi.writeFile(binfile)

##################### write notes into a text file################################
    # Specify the path to save the text file
    text_file_path = 'recognized_notes.txt'

    # Open the text file in write mode
    with open(text_file_path, 'w') as text_file:
        # Write the recognized notes to the text file
        text_file.write('Recognized Notes\n\n')

        # Initialize a counter for total notes
        total_notes = 0

        # Write the notes without their symbols to the text file
        for note_group in note_groups:
            for note in note_group:
                text_file.write(f'{note.note}\n')
                total_notes += 1

        # Write the total number of notes
        text_file.write(f'\nTotal number of notes: {total_notes}\n')

    print(f'Recognized notes saved to {text_file_path}')


##################################midi-to-img#############################################
################################################################################################


    # Assuming you have an instance of the MidiFile class
    midi_sheet = MidiFile(f"{output_sheet_directory}/{img_file_name}_output_sheet.mid")

    # Call the draw_roll_and_save method with a filename (optional)
    get_size = midi_sheet.draw_roll_and_save(f'{img_file_name}_img.png', None)

    # Load audio MIDI file
    midi_audio = MidiFile(f"{audio_output_directory}/{audio_name}_basic_pitch.mid")

    # Call the draw_roll_and_save method with a filename
    midi_audio.draw_roll_and_save(f'{audio_name}_img.png',get_size)

#####################################image processing##############################
    # Process first image
    red_line_a = process_image(f"{img_file_name}_img.png", f"cropped_{img_file_name}_sheet_img")

    # Process second image
    red_line_b = process_image(f"{audio_name}_img.png", f"cropped_{audio_name}_audio_img")

######################################################################################################
    passed_notes = compare_midi_images(red_line_a, red_line_b, mode)

    # Draw rectangle on the failed notes
    result = draw_rectangle_on_failed_notes(whole_recs_img, note_groups,passed_notes)

    # Save the image with drawn rectangle
    cv2.imwrite('result.png', result)

    generate_overlay_image(f"cropped_{audio_name}_audio_img_bitwise.jpg",f"cropped_{img_file_name}_sheet_img_bitwise.jpg")

    # Delete all files in the output_audio directory
    output_audio_dir = "output_audio"
    for filename in os.listdir(output_audio_dir):
        file_path = os.path.join(output_audio_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

######################################compare-midi################################

