import subprocess
import os


def _get_disks():
    disks = list()
    try:
        output = subprocess.check_output(['lsblk', '-io', 'KNAME,TYPE'])
        if output is not None:
            for line in output.splitlines():
                line_segments = line.split(' ')
                if line_segments[len(line_segments) - 1] == 'disk':
                    disks.append(line_segments[0])
    except subprocess.CalledProcessError:
        print ("An error in _get_disks() has ocured: Command 'exit 1' returned non-zero exit status 1")
    return disks


def _get_disk_write_speeds():
    iterations = 1
    speeds = 0
    disks = _get_disks()
    try:
        for disk in disks:
            inner_sum_speed = 0
            err = None
            for i in range(iterations):
                output, err = subprocess.Popen(['sudo', 'dd', 'if=/dev/' + disk, 'of=' + os.path.expanduser('~/disk_benchmark_file'), 'bs=8k', 'count=200k'], stderr=subprocess.PIPE).communicate()
                subprocess.call(['sudo', 'rm', os.path.expanduser('~/disk_benchmark_file')])
                print err
                if err is not None:
                    lines = err.splitlines()
                    line_segments = lines[2].split(' ')
                    speed_in_mbs = line_segments[len(line_segments) - 2]
                    speed_in_bytes = float(speed_in_mbs) * 1000000
                    inner_sum_speed += int(speed_in_bytes)
            if err is not None:
                speeds += inner_sum_speed / iterations
    except subprocess.CalledProcessError:
        print ("An error in _get_disk_write_speeds() has ocured: Command 'exit 1' returned non-zero exit status 1")
    print speeds

if __name__ == '__main__':
    _get_disk_write_speeds()


# import datetime
#
# time_test =datetime.datetime(2016, 11, 07, 19, 05, 31, 000001).isoformat()
# time_now = datetime.datetime.now().isoformat()
#
# print "time test: ", time_test
# print "time now:  ", time_now
#
# if time_test > time_now:
#     print "bigger than"
#     print "Exp: ", time_test
#     print "Now: ", time_now
# else:
#     print "ELSE (not >)"
#     print "Exp: ", time_test
#     print "Now: ", time_now