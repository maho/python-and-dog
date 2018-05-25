import unittest

import config
import main

class RequestStub:
    def __init__(self, json):
        self.json = json


class ThreadsStub:
    def start_new_thread(self, fn, args, kwargs):
        fn(*args, **kwargs)


class TemplatesStub:
    ...


class ConfigStub:
    """ just empty object, to be filled ad-hoc """
    pass


class ServoStub:
    def __init__(self, *args, **kwargs):
        self.init_args = args
        self.init_kwargs = kwargs
        self.used_speeds = []

    def speed(self, speed):
        self.used_speeds.append(speed)


class StdlibStub:
    def __init__(self):
        self.uslept = []

    def sleep(self, time_: float):
        self.uslept.append(time_)

    def init_wifi(self):
        pass  # do nothing in tests

    def init_logging(self):
        pass  # do nothing in tests


class TreatLogicStub:
    def __init__(self):
        self.sizes = []

    def treat(self, sizes: list):
        self.sizes.extend(sizes)


#  TreatApp.treat(POST) -> 
#       TurnLogic.treat(sizes: list of turn sizes) -> 
#           TurnLogic.turn((speed: int, time:float)) -> 
#               Servo.speed(...)


class TestTreatApp(unittest.TestCase):
    def treatApp(self, treat_logic=None, config=None, stdlib=None, templates=None):
        """ instantiate TreatApp with provider specified in params, or stubbed if not
        provided """

        treat_logic = treat_logic or TreatLogicStub()
        config = config or ConfigStub()
        stdlib = stdlib or StdlibStub()
        templates = templates or TemplatesStub()

        return main.TreatApp(treat_logic=treat_logic, config=config, stdlib=stdlib, templates=templates)

    def test_index(self):
        templates = TemplatesStub()
        templates.INDEX = "Cest un index"
        
        app = self.treatApp(templates=templates)
        ret = app.index(req=...)
        self.assertEqual(ret.body, b"Cest un index")
    
    def test_treat_with_portion(self):
        """ check if treating with portion will run TurnLogic.treat(sizes) """
        

        # GIVEN: predefined portion with index '2'
        config = ConfigStub()
        config.PORTION_SIZES = {2: [0.5, 1.0]}
        
        # GIVEN: application with stubbed TreadLogic
        treat_logic = TreatLogicStub()
        app = self.treatApp(treat_logic=treat_logic, config=config)

        # WHEN: asking app for treat with portion=2
        app.treat(RequestStub(json={'portion': 2}))

        # THEN: treat logic is called according to sizes configured in config
        self.assertEqual(treat_logic.sizes, [0.5, 1.0])


    def test_treat_with_sizes(self):
        """ check if treating with specified sizes will pass those sizes into TurnLogic.treat """

        # GIVEN: application with stubbed TreadLogic
        treat_logic = TreatLogicStub()
        app = self.treatApp(treat_logic=treat_logic)

        # WHEN asking app for treat with sizes=-1,1,-1
        app.treat(RequestStub(json={'sizes': "-1,1,-1"}))

        # THEN: treat logic is called with the same sizes
        self.assertEqual(treat_logic.sizes, [-1.0, 1.0, -1.0])



class TestTurnLogic(unittest.TestCase):

    def test_turnlogic_turn(self):
        """ check if calling treatlogic.treat call set of treatlogic.turn """
        
        _turns = []
        def _turn(speed, time):
            _turns.append((speed, time))

        # GIVEN: TURN_SPEED = 1, FULL_ANGLE_TIME=2
        config = ConfigStub()
        config.TURN_SPEED = 1
        config.FULL_ANGLE_TIME = 2
        # GIVEN: real TreatLogic
        treat_logic = main.TreatLogic(config=config, threads=ThreadsStub(), servo=ServoStub(), stdlib=StdlibStub())
        # ... but TreatLogic.turn is mocked with custom function
        treat_logic.turn = _turn

        # WHEN: calling TreatLogic.treat with sizes = [1, -0.5]
        treat_logic.treat([1, -0.5])

        # THEN: turn has been called with speed, times: (1, 2), (-1, 1)
        self.assertEqual(_turns, [(1, 2), (-1, 1)])

    def test_turnlogic_servo(self):
        """ check if calling treatlogic.treat will call Servo speed, wait, and then zero speed """
 
        # GIVEN: servo is stubbed
        servo = ServoStub()
        # ... stdlib abstraction is also stubbed
        stdlib = StdlibStub()
        # and real TreatLogic
        # config is ... config module
        treat_logic = main.TreatLogic(config=config, servo=servo, stdlib=stdlib, threads=ThreadsStub())
 
        # WHEN called TreatLogic.turn(10, 20)
        treat_logic.turn(10, 20)
 
        # THEN: usleep was called with (20)
        self.assertEqual(stdlib.uslept, [20])
        # ... and ServoStub.speed() was called two times , with 10 and with 0
        self.assertEqual(servo.used_speeds, [10, 0])


if __name__ == '__main__':
    unittest.main()
