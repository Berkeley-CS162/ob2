from ob2.util.time import now


class Job(object):
    def __init__(self, build_name, source, trigger, graded=True, debug_mode=False):
        """
        Creates a new dockergrader job to be added to the queue.

        """
        self.build_name = build_name
        self.source = source
        self.trigger = trigger
        self.updated = now()
        self.graded = graded
        self.debug_mode = debug_mode


class JobFailedError(Exception):
    def __init__(self, message, critical=False):
        super(JobFailedError, self).__init__(message)
        self.args = (message, critical)

    def __str__(self):
        return self.args[0]
