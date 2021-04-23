// Copyright Alex Eidt 2021
// Implements several image processing functions such as convolutions, grayscaling and
// conversion to ASCII indexing.

#include "process_image.h"

void process_stream(
    uint8_t* input,
    uint8_t* output,
    int w,
    int h,
    int factor,
    int grayscale,
    bool mirror
) {
    // Code is not refactored to increase performance to avoid if checks in loops.
    if (mirror) {
        if (grayscale == 0) { // Use weighted RGB for grayscaling.
            int index = 0;
            for (int y = 0; y < h; y += factor) {
                for (int x = 0; x < w; x += factor * NUM_CHANNELS) {
                    int i = y*w + w - x;
                    uint8_t R = input[i];
                    uint8_t G = input[i + 1];
                    uint8_t B = input[i + 2];
                    // Grayscale = 0.375 R + 0.5 G + 0.125 B
                    output[index++] = (R + R + R + B + G + G + G + G) >> 3;
                }
            }
        } else if (grayscale == 1) { // Use three way max for grayscaling.
            int index = 0;
            for (int y = 0; y < h; y += factor) {
                for (int x = 0; x < w; x += factor * NUM_CHANNELS) {
                    int i = y*w + w - x;
                    uint8_t R = input[i];
                    uint8_t G = input[i + 1];
                    uint8_t B = input[i + 2];
                    output[index++] = three_way_max(R, G, B);
                }
            } 
        } else { // Show color image.
            int index = 0;
            for (int y = 0; y < h; y += factor) {
                for (int x = 0; x < w; x += factor * NUM_CHANNELS) {
                    int i = y*w + w - x;
                    output[index++] = input[i];
                    output[index++] = input[i + 1];
                    output[index++] = input[i + 2];
                }
            }
        }
    } else {
        if (grayscale == 0) { // Use weighted RGB for grayscaling.
            int index = 0;
            for (int y = 0; y < h; y += factor) {
                for (int x = 0; x < w; x += factor * NUM_CHANNELS) {
                    int i = y*w + x;
                    uint8_t R = input[i];
                    uint8_t G = input[i + 1];
                    uint8_t B = input[i + 2];
                    // Grayscale = 0.375 R + 0.5 G + 0.125 B
                    output[index++] = (R + R + R + B + G + G + G + G) >> 3;
                }
            }
        } else if (grayscale == 1) { // Use three way max for grayscaling.
            int index = 0;
            for (int y = 0; y < h; y += factor) {
                for (int x = 0; x < w; x += factor * NUM_CHANNELS) {
                    int i = y*w + x;
                    uint8_t R = input[i];
                    uint8_t G = input[i + 1];
                    uint8_t B = input[i + 2];
                    output[index++] = three_way_max(R, G, B);
                }
            } 
        } else { // Show color image.
            int index = 0;
            for (int y = 0; y < h; y += factor) {
                for (int x = 0; x < w; x += factor * NUM_CHANNELS) {
                    int i = y*w + x;
                    output[index++] = input[i];
                    output[index++] = input[i + 1];
                    output[index++] = input[i + 2];
                }
            }
        }
    }
}

uint8_t three_way_max(uint8_t a, uint8_t b, uint8_t c)
{
    return (a > b) ? ((a > c) ? a : c) : ((b > c) ? b : c);
}

void ascii(uint8_t* inout, int size) {
    // 93 is number of ASCII characters to choose from.
    for (int i = 0; i < size; i++) {
        inout[i] = 93 - inout[i] * 93 / 255;
        if (inout[i] < 0) inout[i] = 0;
        else if (inout[i] > 92) inout[i] = 92;
    }
}

void apply(uint8_t* input, uint8_t* output, int w, int h, int kernel_type) {
    switch (kernel_type) {
        case OUTLINE: // Outline Kernel
        {
            //const uint8_t kernel[9] =  {-1, -1, -1, -1, 8, -1, -1, -1, -1};
            const uint8_t kernel[9] =  {0, -1, 0, -1, 4, -1, 0, -1, 0};
            convolve(input, output, kernel, w, h);
            break;
        }
        case SHARPEN: // Sharpen Kernel
        {
            const uint8_t kernel[9] =  {0, -1, 0, -1, 5, -1, 0, -1, 0};
            convolve(input, output, kernel, w, h);
            break;
        }
        case EMBOSS: // Emboss Kernel
        {
            const uint8_t kernel[9] =  {-2, -1, 0, -1, 1, 1, 0, 1, 2};
            convolve(input, output, kernel, w, h);
            break;
        }
        case SOBEL: // Sobel Kernels
        {
            sobel(input, output, w, h);
            break;
        }
    }
}

void convolve(
    uint8_t* input,
    uint8_t* output,
    const uint8_t* kernel,
    int w,
    int h
) {
    int index = 0;
    for (int y = 1; y < h - 1; y++) {
        for (int x = 1; x < w - 1; x++) {
            int i = x + y*w;
            int imw = i - w;
            int ipw = i + w;
            output[index++] =
                  kernel[0] * input[imw - 1]
                + kernel[1] * input[imw]
                + kernel[2] * input[imw + 1]
                + kernel[3] * input[i - 1]
                + kernel[4] * input[i]
                + kernel[5] * input[i + 1]
                + kernel[6] * input[ipw - 1]
                + kernel[7] * input[ipw]
                + kernel[8] * input[ipw + 1];
        }
    }
}

int isqrt(int n) {
    int x = n;
    int y = 1;
    while (x > y) {
        x = (x + y) >> 1;
        y = n / x;
    }
    return x;
}

void sobel(uint8_t* input, uint8_t* output, int w, int h)
{
    int index = 0;
    for (int y = 1; y < h - 1; y++) {
        for (int x = 1; x < w - 1; x++) {
            int i = x + y*w;
            int imw = i - w;
            int ipw = i + w;
            int h1 = input[imw - 1] - input[imw + 1];
            int h2 = -input[imw - 1] - 2 * input[imw] - input[imw + 1];
            h1 += 2 * input[i - 1] - 2 * input[i + 1] + input[ipw - 1] - input[ipw + 1];
            h2 += input[ipw - 1] + 2 * input[ipw] + input[ipw + 1];
            output[index++] = isqrt(h1 * h1 + h2 * h2);
        }
    }
}