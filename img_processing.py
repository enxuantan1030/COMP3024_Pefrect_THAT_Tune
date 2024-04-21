import cv2
import numpy as np


def process_image(input_image_path, output_image_path_prefix):
    # Load the image
    img_sheet = cv2.imread(input_image_path)

    # Find black rectangles in the image
    black_rectangles = find_black_rectangles(img_sheet, input_image_path)

    # Crop black rectangle
    cropped_rectangle = crop_black_rectangle(img_sheet, black_rectangles)

    # Save cropped rectangle if it exists
    if cropped_rectangle is not None:
        cv2.imwrite(f"{output_image_path_prefix}_cropped_rectangle.jpg", cropped_rectangle)

    # Stretch the cropped rectangle
    if cropped_rectangle is not None:
        # Reduce noise
        reduced_noise_image = reduce_noise(cropped_rectangle,output_image_path_prefix)
        cv2.imwrite(f"{output_image_path_prefix}_reduced_noise.jpg",reduced_noise_image)

        # Pixelate image
        pixelated_image = pixelate(reduced_noise_image, 5)
        cv2.imwrite(f"{output_image_path_prefix}_pixelated.jpg", pixelated_image)

        img_sheet_cropped_stretched = crop_and_stretch(pixelated_image)
        cv2.imwrite(f"{output_image_path_prefix}_cropped_and_stretched.jpg", img_sheet_cropped_stretched)

        # Detect red lines
        red_lines = detect_red_lines(img_sheet_cropped_stretched)
        red_lines = sorted(red_lines, key=lambda x: x[0])  # Sort red lines by start position

        # Print the total number of red lines detected
        print(f"Total red lines detected: {len(red_lines)}")

        # Calculate the height from the detected red lines
        if red_lines:
            height = red_lines[0][2][1] - red_lines[0][0][1]
        else:
            height = 0

        # Put lines on the start and end positions of all red lines
        for line_num, (start_pos1, start_pos2, end_pos1, end_pos2) in enumerate(red_lines):
            # Draw blue line from first start position to second start position
            cv2.line(img_sheet_cropped_stretched, (start_pos1[0], start_pos1[1]), (start_pos2[0], start_pos2[1]), (255, 255, 255), 2)  # Blue color

            # Draw green line from first end position to second end position
            cv2.line(img_sheet_cropped_stretched, (end_pos1[0], end_pos1[1]), (end_pos2[0], end_pos2[1]), (0, 255, 0),
                     2)  # Green color

        # Save the image with colored lines drawn
        cv2.imwrite(f"{output_image_path_prefix}_detected_lines.jpg", img_sheet_cropped_stretched)

        return red_lines

def reduce_noise(image, filename, morph_kernel_size=5):
    # Convert the image to the HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    cv2.imwrite(f"{filename}_hsv.jpg", hsv)
    # Define lower and upper bounds for red color in HSV
    lower_red = np.array([0, 80, 80])
    upper_red = np.array([10, 255, 255])

    # Create a mask to isolate red color
    red_mask = cv2.inRange(hsv, lower_red, upper_red)
    cv2.imwrite(f"{filename}_red_mask.jpg", red_mask)

    # Apply a morphological operation (opening) to remove small noise
    kernel = np.ones((morph_kernel_size, morph_kernel_size), np.uint8)
    opened_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    cv2.imwrite(f"{filename}_morphology.jpg", opened_mask)

    # Bitwise-AND the original image with the cleaned mask
    # first parameter: source image;
    # second parameter: destination image;
    # third parameter: result image afer performing morphological opening operation;
    result = cv2.bitwise_and(image, image, mask=opened_mask)
    cv2.imwrite(f"{filename}_bitwise.jpg", result)

    return result


def detect_red_lines(image, min_distance=10):
    red_lines = []
    height, width, _ = image.shape
    scanned_positions = set()  # Set to store scanned positions

    # 1. Vertically Search for Red Color (First Start Position)
    for y in range(image.shape[0] - 1, -1, -1):  # Iterate over rows (from bottom to top)
        for x in range(image.shape[1]):  # Iterate over columns (from left to right)
            # Check if the pixel at coordinates (x, y) is red and if it has not been scanned before
            if is_red_pixel(image[y, x]) and (x, y) not in scanned_positions:
                # Record the coordinates as the first start position
                first_start_position = (x, y)
                scanned_positions.add((x, y))  # Add the position to scanned positions

                # Initialize second_start_position and first_end_position
                second_start_position = None
                first_end_position = None

                # 2. Continue Vertically to Find the End of Red Color (Second Start Position)
                for y_end in range(y - 1, -1, -1):  # Continue from first start position upwards
                    if not is_red_pixel(image[y_end, x]):
                        # Record the coordinates as the second end position
                        second_start_position = (x, y_end)
                        break  # Exit the loop once the second end position is found

                # Ensure second_start_position is found before proceeding
                if second_start_position is not None:
                    # 3. Calculate Height
                    height = second_start_position[1] - first_start_position[1]

                    # 4. Horizontal Search for Red Color (First End Position)
                    for x_end in range(x, width):
                        if not is_red_pixel(image[first_start_position[1], x_end]):
                            # Record the coordinates of the last pixel with red color as the first end position
                            first_end_position = (x_end - 1, first_start_position[1])
                            # Store all scanned positions during horizontal search
                            scanned_positions.update((x, first_start_position[1]) for x in range(x, x_end))
                            break

                    # Check if first_end_position is found before proceeding
                    if first_end_position is None:
                        # If the loop completes without finding any non-red pixel,
                        # consider the last pixel in the row as the first end position
                        first_end_position = (width - 1, first_start_position[1])

                    # 5. Calculate Second End Position
                    second_end_position = (first_end_position[0], first_end_position[1] + height)

                    # 6. Check if this line overlaps with any existing line
                    is_overlapping = False
                    for line in red_lines:
                        _, _, existing_end1, existing_end2 = line
                        if abs(existing_end1[0] - first_end_position[0]) < min_distance and \
                                abs(existing_end1[1] - first_end_position[1]) < min_distance and \
                                abs(existing_end2[0] - second_end_position[0]) < min_distance and \
                                abs(existing_end2[1] - second_end_position[1]) < min_distance:
                            is_overlapping = True
                            break

                    # 7. If not overlapping, add the line to red_lines
                    if not is_overlapping:
                        red_lines.append(
                            (first_start_position, second_start_position, first_end_position, second_end_position))

    return red_lines


def is_red_pixel(pixel):
    # Check if the pixel is red based on its HSV values or any other criterion
    # Implement this function according to your requirements
    # For simplicity, we'll assume any pixel with non-zero Red channel is red
    return pixel[2] > 0


def pixelate(image, pixel_size):
    # Resize the image to a smaller size
    small = cv2.resize(image, None, fx=1/pixel_size, fy=1/pixel_size, interpolation=cv2.INTER_NEAREST)

    # Resize the small image back to the original size
    pixelated = cv2.resize(small, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)

    return pixelated


def find_black_rectangles(img, input_image_path):
    # Convert the image to grayscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding to obtain a binary image
    binary_img = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    cv2.imwrite(f"{input_image_path}_binary.jpg", binary_img)

    # Find contours in the binary image
    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on area
    min_contour_area = 100
    black_rectangles = [contour for contour in contours if cv2.contourArea(contour) > min_contour_area]

    # Draw contours on the original image
    img_with_contours = img.copy()
    cv2.drawContours(img_with_contours, black_rectangles, -1, (0, 255, 0), 2)  # Green color, thickness 2
    cv2.imwrite(f"{input_image_path}_contour.jpg", img_with_contours)

    return black_rectangles

def crop_black_rectangle(img, rectangles):
    if rectangles:
        rect = rectangles[0]  # Select the first rectangle found
        x, y, w, h = cv2.boundingRect(rect)
        cropped_rect = img[y:y + h, x:x + w]
        return cropped_rect
    else:
        return None


def crop_and_stretch(img):
    # Find the first and last non-black columns
    non_black_cols = np.where(np.any(img != 0, axis=0))[0]
    if non_black_cols.size:
        start_col = non_black_cols[0]
        end_col = non_black_cols[-1]
    else:
        # If no non-black columns found, return the original image
        return img

    # Crop the image based on the bounding box of non-black regions along the width
    cropped_img = img[:, start_col:end_col + 1]

    # Calculate the original width
    original_width = img.shape[1]

    # Stretch the cropped image horizontally to match the original width
    stretched_img = cv2.resize(cropped_img, (original_width, cropped_img.shape[0]))

    return stretched_img
