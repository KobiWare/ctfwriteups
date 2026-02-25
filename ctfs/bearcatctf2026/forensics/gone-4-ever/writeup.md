---
author: Mills
credit: Mills
---
## Solution
In the ubnutu folder, there are 100 images programmatically downloaded from the site 'https://placehold.co/'. One of them contains the flag embedded in the image (using steghide to embed it)
This is all known via the bash history

To narrow the images down, you can download the same images from the site, and compare file sizes to see which one of the images has a different file size. This will narrow it down to one image

From there, you can use crunch to brutefore the rest (~5 minutes or so). Stegseek doesn't seem to work.

## Flag

`BCCTF{GonE_But_nOt_4GottEn}`
