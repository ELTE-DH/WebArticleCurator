
import sys
import logging
from threading import Thread
from argparse import Namespace
from functools import partial


class Logger:
    """
        Handle logging with Python's built-in logging facilities simplified
    """
    def __init__(self, log_filename=None, logfile_mode='a', logfile_encoding='UTF-8', logfile_level='INFO',
                 console_stream=sys.stderr, console_level='INFO', console_format='{asctime} {levelname}: {message}',
                 file_format='{asctime} {levelname}: {message}'):
        # logging.basicConfig(level=logging.INFO)  # For debugging requests
        log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR,
                      'CRITICAL': logging.CRITICAL}

        if console_level not in log_levels:
            raise KeyError('Console loglevel is not valid ({0}): {1}'.format(', '.join(log_levels.keys()),
                                                                             console_level))
        console_level = log_levels[console_level]

        if logfile_level not in log_levels:
            raise KeyError('Logfile loglevel is not valid ({0}): {1}'.format(', '.join(log_levels.keys()),
                                                                             logfile_level))
        logfile_level = log_levels[logfile_level]

        # Create logger
        self._logger = logging.getLogger(log_filename)  # Logger is named after the logfile
        self._logger.propagate = False

        # Create one handler for console output and set its properties accordingly
        c_handler = logging.StreamHandler(stream=console_stream)
        c_handler.setLevel(console_level)

        # Create formatters and add them to handlers
        c_format = logging.Formatter(console_format, style='{')
        c_handler.setFormatter(c_format)

        # Add handlers to the logger
        self._logger.addHandler(c_handler)

        # Create another handler for the logfile and set its properties accordingly
        if log_filename is not None:
            f_handler = logging.FileHandler(log_filename, mode=logfile_mode, encoding=logfile_encoding)
            f_handler.setLevel(logfile_level)
            f_format = logging.Formatter(file_format, style='{')
            f_handler.setFormatter(f_format)
            self._logger.addHandler(f_handler)

        self._logger.setLevel(min(console_level, logfile_level))

        self._leveled_logger = {'DEBUG': self._logger.debug, 'INFO': self._logger.info, 'WARNING': self._logger.warning,
                                'ERROR': self._logger.error, 'CRITICAL': self._logger.critical}

        # Variables for supporting multiprocess logging
        self._q = None
        self._lp = None

        self.log('INFO', 'Logging started')

    def log(self, level, *message, sep=' ', end='\n', file=None):
        """
            A print()-like logging function
                :param level: (str) Levels from the standard set: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
                :param message: One or more elems as for print()
                :param sep: Separator element as for print()
                :param end: Ending element as for print()
                :param file: Ignored as handlers are set in __init__()
                :return: None
        """
        _ = file  # Silence IDE
        for handler in self._logger.handlers:
            handler.terminator = end
        if level not in self._leveled_logger:
            self._leveled_logger['CRITICAL']('UNKNOWN LOGGING LEVEL SPECIFIED FOR THE NEXT ENTRY: {0}'.format(level))
            level = 'CRITICAL'
        self._leveled_logger[level](sep.join(str(msg) for msg in message))

    @staticmethod
    def _log_to_queue(queue, level, *args, **kwargs):
        queue.put((level, args, kwargs))

    @staticmethod
    def _logger_thread(queue, log_fun):
        while True:
            record = queue.get()
            if record is None:
                break
            level, log_args, log_kwargs = record
            log_fun(level, *log_args, **log_kwargs)  # LOG HERE from init parameter!

    def init_mp_logging_context(self, queue):
        """Create a separate thread for logging through a Queue (see the following example)

            from itertools import repeat
            from multiprocessing import Pool, Manager, current_process

            from logger import Logger

            def worker_process(par):
                state, lq = par
                retl = []
                for n in range(100):
                    lq.log('WARNING', f'{current_process().name} message{state} {n}')
                lq.log('WARNING', f'{current_process().name} finished')
                return retl

            log_obj = Logger('test.log', 'w')  # Apply all parameters for logger here!
            log_obj.log('INFO', 'NORMAL LOG BEGIN')  # Normal logging
            with Manager() as man:
                log_queue = man.Queue()
                with log_obj.init_mp_logging_context(log_queue) as mplogger, Pool() as p:
                    # Here one can log parallel from all processes!
                    return_queue = p.imap(worker_process, zip(range(10), repeat(mplogger)), chunksize=3)
                    for _ in return_queue:
                        pass
            log_obj.log('INFO', 'NORMAL LOG END')  # Normal logging
        """
        self._q = queue
        self._lp = Thread(target=self._logger_thread, args=(self._q, self.log))
        self._lp.start()
        return self

    def __enter__(self):
        """Enter into context with prepared queue"""
        if self._q is None:
            raise RuntimeError('Must call init_mp_logging_context() with an initialised Queue as param'
                               ' before entering into context!')
        return Namespace(log=partial(self._log_to_queue, self._q))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Tell the logging thread to finish up"""
        self._q.put(None)
        self._lp.join()

    def __del__(self):
        handlers = list(self._logger.handlers)  # Copy, because we write the same variable in the loop!
        for h in handlers:
            self._logger.removeHandler(h)
            h.flush()
            if isinstance(h, logging.FileHandler):
                h.close()
