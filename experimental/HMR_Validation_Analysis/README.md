# HMR Stylus Test Evaluation
This CL contains the Python source code for the sliding window algorithm that evaluates stylus tests performed on Human Motion Robots (HMR).

## Installation Guide
This algorithm is developed using Python 3.10.10 ([download link](https://www.python.org/downloads/release/python-31010/)) and requires several libraries in Python to perform curve fitting and graph plotting. These libraries are described in `requirements.txt`. To install these libraries, please run the command:
~~~
pip install -r requirements.txt
~~~

## Running the algorithm
There are a few variables we need to provide for the algorithm to run in `main.py`:
- `refTestDimensions`: The screen dimensions of the reference case
- `resTestDimensions`: The screen dimensions of the result case
- `refCsvFilePath`: The file path to the reference case csv
- `resultCsvFilePath`: The file path to the result case csv
- `calibrationLogPath`: The file path to the calibration log generated from grid calibration ([4915894: platform: HMR Calibration script](https://chromium-review.googlesource.com/c/chromiumos/platform/human_motion_robot/+/4915894))
- `needCurveFittingPlots`: Whether we need to plot curve fitting results or not (There can be a huge number of curve fitting and potentially use up a lot of space)

There are also some constants we can adjust in `HMR_EvaluationConfig.py` that controls how we want to evaluate the test cases using this algorithm including:
- The sliding window size
- The maximum degree that we want to go for polynomial curve fitting
- The threshold of Mean Squared Error to pass / fail test cases

After providing the above variables and constants, simply run the evaluation algorithm by:
~~~
python -u "<directory-of-main.py>/main.py"
~~~
