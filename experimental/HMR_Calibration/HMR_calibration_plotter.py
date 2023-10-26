from HMR_calibration_data   import HMR_EVTestData, HMR_CalibrationCase
from HMR_error_analyzer     import HMR_ErrorAnalyzer
from typing                 import (Tuple, List)
from pathlib                import Path
from plotly.subplots        import make_subplots
import plotly.graph_objects as go


PIXEL = 1/72  # pixel in inches
MAX_FIGURE_X = 150
MAX_FIGURE_Y = 100
IMAGE_FORMAT = 'RGBA'
class HMR_CalibrationPlotter():
    def __init__(self, data:HMR_EVTestData, csvFilePath:str, isSavePlot:bool) -> None:
        self.name = Path(csvFilePath).stem
        self.directory = str(Path(csvFilePath).parent)
        self.caseNames = ['segmented', 'segmented_derotated', 'segmented_derotated_deskewed', 'segmented_calibrated']
        self.data = data
        self.isSavePlot = isSavePlot

    def createSubPlots(self, rows:int, cols:int, subPlotTitles:Tuple[str]) -> go.Figure:
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subPlotTitles
        )
        fig.update_layout(plot_bgcolor="white")
        return fig

    def savePlot(self, fig:go.Figure, destFilePath:str) -> None:
        fig.write_html(f'{destFilePath}.html')
        print(f'[INFO]: Plotted and saved at: {destFilePath}.html')
        img_bytes = fig.to_image(format="png", width=1600, height=900, scale=3)
        with open(f'{destFilePath}.png', "wb") as img:
            img.write(img_bytes)

        print(f'[INFO]: Plotted and saved at: {destFilePath}.png')
        fig = None # delete the fig in the program after saving it

    def setAxes(self, fig:go.Figure, xRange:List[float]|None, xlabel:str, yRange:List[float]|None, ylabel:str, row:int, col:int) -> None:
        fig.update_xaxes(range=xRange, title_text=xlabel, showline=True, linewidth=1, linecolor='black', showgrid=False, ticks='outside', row=row, col=col)
        fig.update_yaxes(range=yRange, title_text=ylabel, showline=True, linewidth=1, linecolor='black', showgrid=False, ticks='outside', row=row, col=col)

    def plotOne(self, case_name:str) -> None:
        testCase:HMR_CalibrationCase = self.data.__getattribute__(case_name)
        xRange = [min(0, testCase.xmin), testCase.xmax]
        yRange = [min(0, testCase.ymin), testCase.ymax]

        fig = self.createSubPlots(
            1, 1,
            (f'{self.name}-{case_name}',)
        )
        fig.update_layout(showlegend=False)

        hoverTemplate = ('<b>x</b>: %{x:.5f}mm<br>'+
                         '<b>y</b>: %{y:.5f}mm')

        for i, calPath in enumerate(testCase.case):
            X, Y = HMR_ErrorAnalyzer.getPathArray(calPath)
            fig.add_trace(
                go.Scatter(x=X, y=Y, mode="lines+markers", name=f'Calibration path {i}', hovertemplate=hoverTemplate),
                row=1,
                col=1,
            )

        if case_name == 'segmented_calibrated':
            self.setAxes(fig, xRange, 'x (mm)', yRange, 'y (mm)', 1, 1)
        else:
            self.setAxes(fig, xRange, 'x (px)', yRange, 'y (px)', 1, 1)
        fig.update_yaxes(autorange="reversed")
        fig.update_traces(marker=dict(size=0.5))
        if self.isSavePlot:
            self.savePlot(fig, f'{self.directory}/{self.name}-{case_name}')

    def plotAll(self) -> None:
        print('Plotting data...')
        for case_name in self.caseNames:
            self.plotOne(case_name)
