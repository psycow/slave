#  -*- coding: utf-8 -*-
#
# E21, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.
from slave.core import Command, InstrumentBase
import slave.iec60488 as iec
from slave.types import Boolean, Float, Integer, Mapping, Set


class Initiate(InstrumentBase):
    """The initiate command layer.

    :param connection: A connection object.

    :ivar continuous: A boolean representing the continuous initiation mode.

    """
    def __init__(self, connection):
        super(Initiate, self).__init__(connection)
        self.continuous_mode = Command(
            ':INIT:CONT?',
            ':INIT:CONT',
            Boolean
        )

    def __call__(self):
        """Initiates one measurement cycle."""
        self.connection.write(':INIT')


class Output(InstrumentBase):
    """The Output command layer.

    :param connection: A connection object.

    :ivar gain: The analog output gain. A float between -100e6 and 100e6.
    :ivar offset: The analog output offset. -1.2 to 1.2.
    :ivar state: The analog output state. A boolean, `True` equals to on,
        `False` to off.
    :ivar relative: If `True`, the present analog output voltage is used as the
        relative value.

    """
    def __init__(self, connection):
        super(Output, self).__init__(connection)
        self.gain = Command(
            'OUTP:GAIN?',
            'OUTP:GAIN',
            Float(min=-100e6, max=100e6)
        )
        self.offset = Command(
            'OUTP:OFFS?',
            'OUTP:OFFS',
            Float(min=-1.2, max=1.2)
        )
        self.relative = Command(
            'OUTP:REL?',
            'OUTP:REL',
            Boolean
        )
        self.state = Command(
            'OUTP:STAT?',
            'OUTP:STAT',
            Boolean
        )


class Sense(InstrumentBase):
    """The Sense command layer.

    :param connection: A connection object.

    :ivar function: The sense function, either 'temperature' or 'voltage' (dc).

    """
    def __init__(self, connection):
        super(Sense, self).__init__(connection)
        self.function = Command(
            ':SENS:FUNC?',
            ':SENS:FUNC',
            Mapping({'voltage': '"VOLT:DC"', 'temperature': '"TEMP"'})
        )


class Trigger(InstrumentBase):
    """The Trigger command layer.

    :param connection: A connection object.

    :ivar auto_delay: The state of the auto delay.
    :ivar delay: The trigger delay, between 0 to 999999.999 seconds.
    :ivar source: The trigger source, either 'immediate', 'timer', 'manual',
        'bus' or 'external'.
    :ivar timer: The timer interval, between 0 to 999999.999 seconds.

    """
    def __init__(self, connection):
        super(Trigger, self).__init__(connection)
        self.auto_delay = Command(
            ':TRIG:DEL:AUTO?',
            ':TRIG:DEL:AUTO',
            Boolean
        )
        # TODO count has a max value of 9999 but supports infinity as well.
        self.count = Command(
            ':TRIG:COUN?',
            ':TRIG:COUN',
            Float(min=0.)
        )
        self.delay = Command(
            ':TRIG:DEL?',
            ':TRIG:DEL',
            Float(min=0., max=999999.999)
        )
        self.source = Command(
            ':TRIG:SOUR?',
            ':TRIG:SOUR',
            Mapping({'immediate': 'IMM', 'timer': 'TIM', 'manual': 'MAN',
                     'bus': 'BUS', 'external': 'EXT'})
        )
        self.timer = Command(
            ':TRIG:TIM?',
            ':TRIG:TIM',
            Float(min=0., max=999999.999)
        )

    def signal(self):
        """Generates an event, to bypass the event detector block.

        If the trigger system is waiting for an event (specified by the
        :attr:.`source` attribute), the event detection block is immediately
        exited.

        """
        self.connection.write(':TRIG:SIGN')


class Unit(InstrumentBase):
    """The unit command layer.

    :param connection: A connection object.

    :ivar temperature: The unit of the temperature, either 'C', 'F', or 'K'.

    """
    def __init__(self, connection):
        super(Unit, self).__init__(connection)
        self.temperature = Command(
            ':UNIT:TEMP?',
            ':UNIT:TEMP',
            Set('C', 'F', 'K')
        )


class K2182(iec.IEC60488, iec.StoredSetting, iec.Trigger):
    """A keithley model 2182/A nanovoltmeter.

    :param connection: A connection object

    :ivar initiate: An instance of :class:`.Initiate`.
    :ivar output: An instance of :class:`.Output`.
    :ivar sample_count: The sample count. Valid entries are 1 to 1024.
    :ivar temperature: Performs a single-shot measurement of the temperature.

        ..note:: This Command is much slower than :meth:`.read`.

    :ivar triggering: An instance of :class:`.Trigger`.
    :ivar unit: An instance of :class:`.Unit`.
    :ivar voltage: Performs a single-shot measurement of the voltage.

        ..note:: This Command is much slower than :meth:`.read`.

    """
    def __init__(self, connection):
        super(K2182, self).__init__(connection)
        self.initiate = Initiate(connection)
        self.output = Output(connection)
        self.sample_count = Command(
            ':SAMP:COUN?',
            ':SAMP:COUN',
            Integer(min=1, max=1024)
        )
        self.sense = Sense(connection)
        self.temperature = Command((':MEAS:TEMP?', Float))
        self.triggering = Trigger(connection)
        self.unit = Unit(connection)
        self.voltage = Command((':MEAS:VOLT?', Float))

    def abort(self):
        """Resets the trigger system, it put's the device in idle mode."""
        self.connection.write(':ABOR')

    def fetch(self):
        """Returns the latest available reading

        .. note:: It does not perform a measurement.

        """
        # TODO check if it can return multiple values.
        return float(self.connection.ask(':FETC?'))

    def read(self):
        """A high level command to perform a singleshot measurement.

        It resets the trigger model(idle), initiates it, and fetches a new
        value.

        """
        return float(self.connection.ask(':READ?'))
