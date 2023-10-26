from HMR_Data                   import *
from HMR_CurveFitting           import HMR_LeastSquareRegressionCurveFitting
from HMR_EvaluationConfig       import PLOT_FORMAT, PLOT_BGCOLOR, PLOT_SHOWGRID, PLOT_TICKS_LOCATION
from HMR_EvaluationLogger       import HMR_EvaluationLogger
from typing                     import (Tuple, List)
from math                       import (floor, ceil)
from pathlib                    import Path
from plotly.subplots            import make_subplots
import plotly.graph_objects     as go
import os


class HMR_TestCasePlotter():
    def __init__ (
            self,
            refTestCase:HMR_TestCase,
            resTestCase:HMR_TestCase,
            caseResult:HMR_CaseResult,
            logger: HMR_EvaluationLogger,
            testPath:str,
            needCurveFitting:bool = False
        ) -> None:
        self.refTestCase = refTestCase
        self.resTestCase = resTestCase
        self.caseResult = caseResult
        self.needCurveFitting = needCurveFitting
        self.logger = logger

        self.destinationPath = f'{str(Path(testPath).parent)}/plots'
        self.name = Path(testPath).stem
        self.createDirectories()

    def createDirectories(self):
        # Create directory to store images if not exist:
        if not os.path.exists(self.destinationPath):
            os.makedirs(self.destinationPath)

        if self.caseResult is None:
            return

        for i in range(len(self.caseResult.pathResults)):
            if not os.path.exists(f'{self.destinationPath}/path{i}'):
                os.makedirs(f'{self.destinationPath}/path{i}')

            if self.needCurveFitting and not os.path.exists(f'{self.destinationPath}/path{i}/curveFittings'):
                os.makedirs(f'{self.destinationPath}/path{i}/curveFittings')

    def getTestCaseData(self, testCase:HMR_TestCase) -> Tuple[List[float]]:
        x_arr = [None]*(testCase.length)
        y_arr = [None]*(testCase.length)
        extraText = [None]*(testCase.length)
        idx = 0
        for path in testCase.paths:
            curr = path.getStart()
            while curr != path.points_tail:
                x_arr[idx] = curr.coorX
                y_arr[idx] = curr.coorY
                extraText[idx] = f'<b>pressure</b>: {curr.pressure:.5f}<br><b>time</b>: {curr.timeMs:.5f}ms'
                curr = curr.next
                idx += 1

        return x_arr, y_arr, extraText

    def getPathData(self, path:HMR_Path) -> Tuple[List[float], List[float]]:
        curr = path.getStart()
        x = [None]*path.length
        y = [None]*path.length
        extraText = [None]*path.length
        i = 0
        while curr != path.points_tail:
            x[i] = curr.coorX
            y[i] = curr.coorY
            extraText[i] = f'<b>pressure</b>: {curr.pressure:.5f}<br><b>time</b>: {curr.timeMs:.5f}ms'
            curr = curr.next
            i += 1

        return x, y, extraText

    def createSubPlots(self, rows:int, cols:int, subPlotTitles:Tuple[str]) -> go.Figure:
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subPlotTitles
        )
        fig.update_layout(plot_bgcolor=PLOT_BGCOLOR)
        return fig

    def savePlot(self, fig:go.Figure, destFilePath:str) -> None:
        fig.write_html(destFilePath)
        self.logger.info(f'Plotted and saved at: {destFilePath}')
        fig = None # delete the fig in the program after saving it

    def setAxes(self, fig:go.Figure, xRange:List[float]|None, xlabel:str, yRange:List[float]|None, ylabel:str, row:int, col:int) -> None:
        fig.update_xaxes(range=xRange, title_text=xlabel, showline=True, linewidth=1, linecolor='black', showgrid=PLOT_SHOWGRID, ticks=PLOT_TICKS_LOCATION, row=row, col=col)
        fig.update_yaxes(range=yRange, title_text=ylabel, showline=True, linewidth=1, linecolor='black', showgrid=PLOT_SHOWGRID, ticks=PLOT_TICKS_LOCATION, row=row, col=col)

    def plotOverallResult(self) -> None:
        fig = self.createSubPlots(
            3, 2,
            (
                "Trend of offset average",
                "Trend of R<sup>2</sup> average",
                "Trend of offset standard deviation",
                "Trend of R<sup>2</sup> standard deviation",
                "Trend of maximum offset",
                "Trend of minimum R<sup>2</sup>",
            )
        )
        fig.update_layout(showlegend=False)

        # attribute name, plot name, y axis label
        dataInfo = [
            ('offsetMean',  'Offset average',                   'Offset average (mm)',              1, 1),
            ('offsetStd',   'Offset standard deviation',        'Offset standard deviation (mm)',   2, 1),
            ('offsetMax',   'Maximum offset',                   'Maximum offset (mm)',              3, 1),
            ('R2Mean',      'R<sup>2</sup> average',            'R<sup>2</sup> average',            1, 2),
            ('R2Std',       'R<sup>2</sup>standard deviation',  'R<sup>2</sup> standard deviation', 2, 2),
            ('R2Min',       'Minimum R<sup>2</sup>',            'Minimum R<sup>2</sup>',            3, 2),
        ]

        x = [i for i in range(len(self.refTestCase.paths))] # all plots have the same x range
        for (attrName, plotName, yLabel, row, col) in dataInfo:
            hoverTemplate = ('<b>Path</b>: %{x}<br>'+
                             f'<b>{yLabel}</b>: ' + '%{y:.5f}')
            attr = self.caseResult.getAttrFromAllValidPath(attrName)
            fig.add_trace(
                go.Scatter(x=x, y=attr, mode="lines+markers", name=plotName, marker_color='#025464', hovertemplate=hoverTemplate),
                row=row,
                col=col,
            )
            self.setAxes(fig, [0, None], "Valid path ID", [0, None], yLabel, row, col)
        self.savePlot(fig, f'{self.destinationPath}/{self.name}_overall_result.{PLOT_FORMAT}')

    def plotReferenceVsResult(self) -> None:
        fig = self.createSubPlots(1, 1, ("Corrected Reference vs Corrected Result",))

        dataInfo = [
            ('refTestCase', 'Reference',    '#025464'),
            ('resTestCase', 'Result',       '#E57C23'),
        ]

        hoverTemplate = ('<b>x</b>: %{x:.5f}mm<br>'+
                         '<b>y</b>: %{y:.5f}mm<br>'+
                         '%{text}')

        for (attr, plotName, color) in dataInfo:
            x_arr, y_arr, extraText = self.getTestCaseData(self.__getattribute__(attr))
            fig.add_trace(
                go.Scatter(x=x_arr, y=y_arr, mode="markers", name=plotName, marker_color=color, hovertemplate=hoverTemplate, text=extraText),
                row=1,
                col=1
            )

        dutSizeX, dutSizeY = self.refTestCase.getScreenSize()
        self.setAxes(fig, [0, dutSizeX], "x (mm)", [0, dutSizeY], "y (mm)", 1, 1)
        self.savePlot(fig, f'{self.destinationPath}/{self.name}.{PLOT_FORMAT}')

    def plotPathResult(self, path_idx:int, refPath:HMR_Path, resPath:HMR_Path, pathResult:HMR_PathResult) -> None:
        fig = self.createSubPlots(
            3, 2,
            (
                f'Path {path_idx}',
                'No. of steps vs. no. of curve fitting',
                'Current window sizes vs. no. of curve fitting',
                'No. of reference and result points vs. no. of curve fitting',
                'Trend of squared errors: (y<sub>result</sub> - f(x<sub>result</sub>))<sup>2</sup> or (x<sub>result</sub> - f(y<sub>result</sub>))<sup>2</sup>',
                'R<sup>2</sup> of curve fitting vs. reference points',
            )
        )
        fig.update_layout(showlegend=False)

        ref_x, ref_y, refExtraText = self.getPathData(refPath)
        res_x, res_y, resExtraText = self.getPathData(resPath)
        dataInfo = [
            (
                [
                    (ref_x, ref_y, '#025464', 'Reference', refExtraText),
                    (res_x, res_y, '#E57C23', 'Result', resExtraText),
                ],
                'x (mm)', 'y (mm)', 1, 1
            ),
            (
                [
                    (pathResult.nCalculation, pathResult.nSteps, '#025464', 'No. of steps vs. no. of curve fitting', None)
                ],
                'no. of curve fitting', 'no. of steps', 1, 2
            ),
            (
                [
                    ([i for i in range(len(pathResult.currWindowSize))], pathResult.currWindowSize, '#025464', 'Current window sizes', None)
                ],
                'no. of curve fitting', 'no. of reference points', 2, 1
            ),
            (
                [
                    ([i for i in range(len(pathResult.nRefPoints))], pathResult.nRefPoints, '#025464', 'No. of reference points', None),
                    ([i for i in range(len(pathResult.nResPoints))], pathResult.nResPoints, '#E57C23', 'No. of result points', None)
                ],
                'no. of curve fitting', 'no. of points', 2, 2
            ),
            (
                [
                    ([i for i in range(len(pathResult.squaredError))], pathResult.squaredError, '#025464', 'Squared Error', None)
                ],
                'no. of curve fitting', 'squared error (mm<sup>2</sup>)', 3, 1
            ),
            (
                [
                    ([i for i in range(len(pathResult.R2))], pathResult.R2, '#025464', 'R<sup>2</sup>', None)
                ],
                'no. of curve fitting', 'R<sup>2</sup>', 3, 2
            )
        ]

        for (subplot, xLabel, yLabel, row, col) in dataInfo:
            for (x, y, markerColor, plotName, extraText) in subplot:
                hoverTemplate = (f'<b>{xLabel}</b>: ' + '%{x:.5f}<br>'+
                                 f'<b>{yLabel}</b>: ' + '%{y:.5f}')
                if extraText is not None:
                    hoverTemplate += '<br>%{text}'
                fig.add_trace(
                    go.Scatter(x=x, y=y, mode="lines+markers", name=plotName, marker_color=markerColor, hovertemplate=hoverTemplate, text=extraText),
                    row=row,
                    col=col,
                )
            self.setAxes(fig, None, xLabel, None, yLabel, row, col)
        self.savePlot(fig, f'{self.destinationPath}/path{path_idx}/{self.name}_path_{path_idx}_result.{PLOT_FORMAT}')

    def plotWindow(self, path_idx:int, curveFittingResult:HMR_CurveFittingResult) -> None:
        fig = self.createSubPlots(
            1, 1,
            (f'Curve fitting of sliding bubble at path {path_idx}, step {curveFittingResult.step}, calculation {curveFittingResult.calculationNumber}',)
        )
        fig.update_layout(margin=dict(b=200))

        if curveFittingResult.isInverted:
            line_y = [v for v in range(floor(curveFittingResult.min_y), ceil(curveFittingResult.max_y + 1))]
            line_x = HMR_LeastSquareRegressionCurveFitting.roundedPolyVal(line_y, curveFittingResult.coefficients)
        else:
            line_x = [v for v in range(floor(curveFittingResult.min_x), ceil(curveFittingResult.max_x + 1))]
            line_y = HMR_LeastSquareRegressionCurveFitting.roundedPolyVal(line_x, curveFittingResult.coefficients)

        dataInfo = [
            (curveFittingResult.ref_x,  curveFittingResult.ref_y,   'lines+markers',    'Reference',    '#025464'),
            (curveFittingResult.res_x,  curveFittingResult.res_y,   'lines+markers',    'Result',       '#E57C23'),
            (line_x,                    line_y,                     'lines',            'Fitted curve', '#4682A9'),
        ]

        hoverTemplate = ('<b>x</b>: %{x:.5f}mm<br>'+
                         '<b>y</b>: %{y:.5f}mm')

        for (x, y, mode, plotName, color) in dataInfo:
            fig.add_trace(
                go.Scatter(x=x, y=y, mode=mode, name=plotName, marker_color=color, hovertemplate=hoverTemplate),
                row=1,
                col=1
            )
        self.setAxes(fig, None, "x (mm)", None, "y (mm)", 1, 1)

        curve = f'Curve fitting: '
        if curveFittingResult.isInverted:
            curve += 'f(y) = '
            for k, c in enumerate(curveFittingResult.coefficients):
                curve += '+' if c > 0 else ''
                curve += f'{round(c, 3)}y<sup>{k}</sup>'
            squareErrorFormula = '(x<sub>result</sub> - f(y<sub>result</sub>))<sup>2</sup>'
        else:
            curve += 'f(x) = '
            for k, c in enumerate(curveFittingResult.coefficients):
                curve += '+' if c > 0 else ''
                curve += f'{round(c, 3)}x<sup>{k}</sup>'
            squareErrorFormula = '(y<sub>result</sub> - f(x<sub>result</sub>))<sup>2</sup>'
        curve += '<br>'

        text = (curve +
                f'R<sup>2</sup> = {round(curveFittingResult.R2, 3)}<br>' +
                f'Sum of squared error ({squareErrorFormula}) = {round(curveFittingResult.error, 3)}<br>' +
                f'Current max window size = {curveFittingResult.maxWindowSize}<br>' +
                f'Current no. of reference points = {len(curveFittingResult.ref_x)}<br>' +
                f'Current no. of result points = {len(curveFittingResult.res_x)}')

        fig.add_annotation(
            text=text,
            align='left',
            showarrow=False,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="top",
            x=0,
            y=-0.1,
            bordercolor='black',
            borderwidth=1
        )
        self.savePlot(fig, f'{self.destinationPath}/path{path_idx}/curveFittings/{self.name}_path_{path_idx}_step_{curveFittingResult.step}.{PLOT_FORMAT}')

    def plotAll(self):
        self.plotReferenceVsResult()
        self.plotOverallResult()
        for i, (refPath, resPath, pathResult) in enumerate(zip(self.refTestCase.paths, self.resTestCase.paths, self.caseResult.pathResults)):
            self.plotPathResult(i, refPath, resPath, pathResult)
            if self.needCurveFitting:
                for curveFittingResult in pathResult.curveFittings:
                    self.plotWindow(i, curveFittingResult)
