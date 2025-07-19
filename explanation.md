# Analysis of the `doCalculations_custom` function

## Problem

The `doCalculations_custom` function in `DL_Track_US/gui_helpers/do_calculations.py` is responsible for calculating muscle architecture parameters from ultrasound images. Part of this process involves creating a binary mask of the region of interest (ROI) between the superficial and deep aponeuroses.

The user reported that when applying and superimposing the mask on the original ultrasound image, the mask appears to be shifted to the left.

## Root Cause

The error is in the section of the code that generates the `ex_mask`. The logic incorrectly assumes that the x-coordinates of the upper and lower aponeuroses are aligned.

The problematic code is:

```python
ex_mask = np.zeros(thresh.shape, np.uint8)
ex_1 = 0
ex_2 = np.minimum(len(low_x), len(upp_x))

for ii in range(ex_1, ex_2):    #Barrido columna por columna
    ymin = int(np.floor(upp_y_new[ii]))
    ymax = int(np.ceil(low_y_new[ii]))

    ex_mask[:ymin, ii] = 0    #Sobre la apo. superficial
    ex_mask[ymax:, ii] = 0    #Debajo de la apo. profunda
    ex_mask[ymin:ymax, ii] = 255    #Entre las apos.
```

The loop iterates from `0` to `min(len(low_x), len(upp_x))`, using the loop variable `ii` as an index for both `upp_y_new` and `low_y_new`. However, `upp_x` and `low_x` are not guaranteed to have the same starting x-coordinate or the same length. This means that `upp_x[ii]` and `low_x[ii]` could correspond to different columns in the image, causing a shift in the generated mask.

## Proposed Solution

To fix this, the mask generation logic should be updated to correctly map the y-coordinates of the aponeuroses to the corresponding x-coordinates in the image.

The proposed solution involves the following steps:

1.  Find the overlapping range of x-coordinates between the two aponeuroses.
2.  Create interpolation functions for both aponeuroses to get the y-coordinates for any given x-coordinate.
3.  Iterate through the overlapping x-coordinates and fill the mask column by column.

This is the corrected code:

```python
# Creacion de mascara ROI que solo contenga el Musculo limitado por sus aponeurosis
ex_mask = np.zeros(thresh.shape, np.uint8)

# Create interpolation functions for both aponeuroses
f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))

# Determine the overlapping x-range
start_x = int(max(np.min(upp_x), np.min(low_x)))
end_x = int(min(np.max(upp_x), np.max(low_x)))

for x in range(start_x, end_x):
    ymin = int(np.floor(f_upp(x)))
    ymax = int(np.ceil(f_low(x)))

    # Ensure ymin and ymax are within the image bounds
    ymin = max(0, ymin)
    ymax = min(ex_mask.shape[0], ymax)

    ex_mask[ymin:ymax, x] = 255
```
This change will ensure that the mask is generated correctly, aligning with the aponeuroses in the original image.
