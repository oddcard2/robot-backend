from aiohttp import web
from gpiozero import Device, Servo, OutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

a_in1 = None
a_in2 = None
pwm_a = None

b_in1 = None
b_in2 = None
pwm_b = None

async def get_status(request):
    data = {
        'a': {
            'mode': get_side_mode('a', a_in1, a_in2), # off, forward, backward
            'speed': get_speed(pwm_a) # 0-100
        },
        'b': {
            'mode': get_side_mode('b', b_in1, b_in2),
            'speed': get_speed(pwm_b)
        }
    }
    return web.json_response(data)

def get_side_mode(side, in1, in2):
    if in1.value == 0 and in2.value == 0:
        return 'off'
    elif in1.value == 1 and in2.value == 0:
        return 'forward' if side == 'b' else 'backward'
    elif in1.value == 0 and in2.value == 1:
        return 'backward' if side == 'b' else 'forward'
    else:
        return 'invalid'

def get_speed(pwm):
    return int((pwm.value + 1.) * 50.)

def set_side_mode(side, in1, in2, mode):
    if mode == 'off':
        in1.off()
        in2.off()
    elif (mode == 'forward' and side == 'b') or (mode == 'backward' and side == 'a'):
        in1.on()
        in2.off()
    else:
        in1.off()
        in2.on()

async def set_mode(request):
    side = request.match_info['side']
    mode = request.match_info['mode']
    
    if 'a' in side:
        set_side_mode('a', a_in1, a_in2, mode)
    if 'b' in side:
        set_side_mode('b', b_in1, b_in2, mode)
    return web.Response(text='')

async def set_speed(request):
    side = request.match_info['side']
    speed = int(request.match_info['speed'])
    if speed < 0 or speed > 100:
        raise aiohttp.web.HTTPBadRequest()
    speed /= 50. # 0 - 2.
    speed -= 1. # to get value in [-1,1] 

    if 'a' in side:
        pwm_a.value = speed
    if 'b' in side:
        pwm_b.value = speed
    return web.Response(text='')

async def rotate(request):
    direction = request.match_info['direction']
    if direction == 'right':
        set_side_mode('a', a_in1, a_in2, 'backward')
        set_side_mode('b', b_in1, b_in2, 'forward')
    else:
        set_side_mode('a', a_in1, a_in2, 'forward')
        set_side_mode('b', b_in1, b_in2, 'backward')
    return web.Response(text='')

async def root_handler(request):
    return web.HTTPFound('/index.html')

app = web.Application()
app.add_routes([
    web.get('/status', get_status),
    web.post('/{side:a|b|ab}/mode/{mode:off|forward|backward}', set_mode),
    web.post('/{side:a|b|ab}/speed/{speed:\d+}', set_speed),
    web.post('/ab/rotation/{direction:left|right}', rotate),
    web.get('/', root_handler),
    web.static('/', 'dist')
])

if __name__ == '__main__':
    Device.pin_factory = PiGPIOFactory()

    a_in1 = OutputDevice(20)
    a_in2 = OutputDevice(21)

    b_in1 = OutputDevice(5)
    b_in2 = OutputDevice(6)

    pwm_a = Servo(12, max_pulse_width=10/1000)
    pwm_a.value = 0.

    pwm_b = Servo(13, max_pulse_width=10/1000)
    pwm_b.value = 0.

    web.run_app(app)

