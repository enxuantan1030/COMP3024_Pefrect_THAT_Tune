import cv2
import numpy as np


def compare_midi_images(imageA_lines, imageB_lines, mode):
    fail_count = 0
    pass_count = 0
    pass_indices = []  # To store the indices of passed lines

    if mode == 1:
        # Iterate through red lines in imageA
        for i, lineA in enumerate(imageA_lines):
            # Flag to track if a matching line is found
            match_found = False

            # Iterate through red lines in imageB
            for j, lineB in enumerate(imageB_lines):
                # Condition 1: Mode 1 comparison
                if (lineA[0][1] == lineB[0][1] or lineA[2][1] == lineB[2][1]) and \
                        max(min(lineA[0][0], lineA[2][0]), min(lineB[0][0], lineB[2][0])) <= min(
                            max(lineA[0][0], lineA[2][0]), max(lineB[0][0], lineB[2][0])):
                    # If conditions are met, mark this line as pass
                    print('PASS')
                    pass_count += 1
                    match_found = True
                    pass_indices.append(i)  # Append the index of the passed line
                    break

            if not match_found:
                # If no matching line found in imageB, mark this line as fail
                print("FAIL")
                fail_count += 1

    elif mode == 2:
        # Iterate through red lines in imageA and imageB to compare line by line
        for i, (lineA, lineB) in enumerate(zip(imageA_lines, imageB_lines)):
            # Condition 2: Mode 2 comparison
            if (lineA[0][1] == lineB[0][1] or lineA[2][1] == lineB[2][1]) and \
                    lineA[0][1] <= lineB[0][1]:  # Condition for order
                print('PASS')
                pass_count += 1
                pass_indices.append(i)  # Append the index of the passed line

            else:
                print("FAIL")
                fail_count += 1

    print(f"PASS: {pass_count}, FAIL: {fail_count}")

    with open('red_lines_image_a.txt', 'w') as file_a:
        for line_num, (x1_a, y1_a, x2_a, y2_a) in enumerate(imageA_lines):
            file_a.write(f"Red Line {line_num + 1}:\n")
            file_a.write(f"Start Position 1: {x1_a}\n")
            file_a.write(f"Start Position 2: {x2_a}\n")
            file_a.write(f"End Position 1: {y1_a}\n")
            file_a.write(f"End Position 2: {y2_a}\n")
            file_a.write("\n")

    # Save red line coordinates for image B
    with open('red_lines_image_b.txt', 'w') as file_b:
        for line_num, (x1_b, y1_b, x2_b, y2_b) in enumerate(imageB_lines):
            file_b.write(f"Red Line {line_num + 1}:\n")
            file_b.write(f"Start Position 1: {x1_b}\n")
            file_b.write(f"Start Position 2: {x2_b}\n")
            file_b.write(f"End Position 1: {y1_b}\n")
            file_b.write(f"End Position 2: {y2_b}\n")
            file_b.write("\n")

    return pass_indices # Return the list of fail indices


def draw_rectangle_on_failed_notes(img, note_groups, passed_notes):
    # Flatten the note groups to obtain a single list of all notes
    all_notes = [note for note_group in note_groups for note in note_group]

    # Iterate through all notes and draw rectangles on the ones not in passed_notes
    for note in all_notes:
        # Check if the note index is not in the passed_notes list
        if all_notes.index(note) not in passed_notes:
            # Retrieve the bounding box of the note
            note_rect = note.rec  # Assuming 'rec' attribute contains the Rectangle object

            # Draw a red rectangle around the bounding box of the note
            cv2.rectangle(img, (int(note_rect.x), int(note_rect.y)),
                          (int(note_rect.x + note_rect.w), int(note_rect.y + note_rect.h)),
                          (0, 0, 255), 2)  # Red color, thickness 2

    # Return the modified image
    return img


def generate_overlay_image(image_A, image_B):
    img1 = cv2.imread(image_A)
    img2 = cv2.imread(image_B)
    dst = cv2.addWeighted(img1, 0.5, img2, 0.7, 0)

    img_arr = np.hstack((img1, img2))

    # Save the image with drawn rectangle
    cv2.imwrite('overlay.png', dst)