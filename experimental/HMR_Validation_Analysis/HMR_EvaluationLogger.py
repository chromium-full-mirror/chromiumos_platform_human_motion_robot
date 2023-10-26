from pathlib    import Path
import logging


class HMR_EvaluationLogger():
    def __init__(self, logfilePath:str) -> None:
        self.destFolder = str(Path(logfilePath).parent)
        self.name = Path(logfilePath).stem

        logging.basicConfig(
            filename=f'{self.destFolder}/{self.name}.log',
            filemode='w',
            level=logging.DEBUG,
            format='[%(asctime)s - %(levelname)s]: %(message)s'
        )

        self.logger = logging.getLogger()

    def info(self, msg:str) -> None:
        self.logger.info(msg)
        print(f'[INFO]: {msg}')

    def error(self, msg:str) -> None:
        self.logger.error(msg)
        print(f'[ERRO]: {msg}')

    def warning(self, msg:str) -> None:
        self.logger.warning(msg)
        print(f'[WARN]: {msg}')

    def debug(self, msg:str) -> None:
        self.logger.debug(msg)
        print(f'[DEBG]: {msg}')

    def critical(self, msg:str) -> None:
        self.critical(msg)
        print(f'[CRIT]: {msg}')

    def saveOverallAnalysisTable(self, table:str) -> None:
        self.info('\n' + table)

        log = open(f"{self.destFolder}/{self.name}_TableOfOverallAnalysis.log", "w")
        log.write(table)
        log.close()
        self.info(f'Overall analysis table is saved at {self.destFolder}/{self.name}_TableOfOverallAnalysis.log')
