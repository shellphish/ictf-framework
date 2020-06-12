from settings import LOGSTASH_IP, LOGSTASH_PORT
import settings

import json
import logging
import logstash
import subprocess
import threading
import time
import traceback

ERROR_SCRIPT_EXECUTION = (0x100, "Script execution failed.")
ERROR_WRONG_FLAG       = (0x100, "Incorrect flag.")
ERROR_MISSING_FLAG     = (0x101, "Missing 'FLAG' field.")
ERROR_DB               = (0x102, "DB error.")
ERROR_SCRIPT_KILLED    = (0x103, "Script was killed by the scheduler.")

class SchedulerError(Exception):
    pass

class ScriptExecError(Exception):
    pass

class ScriptThread(threading.Thread):

    def __init__(
            self,
            team_id,
            execution_id,
            script_id,
            service_id,
            service_name,
            script_image_path,
            script_type,
            script_name,
            ip, port,
            db_client,
            tick_id,
            delay=0,
            setflag_lock=None,
        ):

        # Initialize thread stuff
        threading.Thread.__init__(self)

        # Make instance vars out of arguments
        self.delay             = delay
        self.setflag_lock      = setflag_lock
        self.execution_id      = execution_id
        self.ip                = ip
        self.port              = port
        self.db                = db_client
        self.team_id           = team_id
        self.script_id         = script_id
        self.service_id        = service_id
        self.service_name      = service_name
        self.script_image_path = script_image_path
        self.script_type       = script_type
        self.script_name       = script_name
        self.tick_id           = tick_id

        # More instance vars
        self.flag_meta = {}
        self.result = {'error': 0, 'error_msg': 'Init'}
        self.max_output_send_bytes = settings.MAX_SCRIPT_OUTPUT_BYTES

        # Set logger
        self.log = logging.getLogger('scriptbot.script_exec')
        self.log.setLevel(settings.LOG_LEVEL)
        self.log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))
        self.log.info('ScriptThread Init')


    def get_status(self):
        """ Used for printing information to the logs"""
        return str({
            'team_id'     : self.team_id,
            'script_id'   : self.script_id,
            'script_type' : self.script_type,
            'dest_ip'     : self.ip,
            'dest_port'   : self.port,
            'delay'       : self.delay,
            'service'     : self.service_name
        })


    def run(self):
        self.log.info(
            "[script %d] Running. (script type: %s, target IP: %s, "
            "target port: %d, delay: %.2f s)" % (
                self.script_id,
                self.script_type,
                self.ip,
                self.port,
                self.delay
            )
        )

        # Sleep thread to randomize run-time during tick
        time.sleep(self.delay)

        # "getflag" should only be run after setflag is done
        if self.script_type == 'getflag':
            start = time.time()
            self.log.info("[script %d] Waiting for setflag script to terminate..." % self.script_id)
            self.setflag_lock.acquire()
            self.log.info(
                "[script %d] setflag script terminated. "
                "Took %f seconds to wait for the lock." % (
                    self.script_id,
                    time.time() - start
                ))

            # "getflag" isn't a "setflag" so release the lock before running
            try: self.setflag_lock.release()
            except threading.ThreadError: pass

        # Run the script
        try:
            self.run_script()
            if self.script_type == 'setflag':
                try: self.setflag_lock.release()
                except threading.ThreadError: pass

        except Exception:
            # Make sure the lock is released
            if self.script_type == "setflag":
                try: self.setflag_lock.release()
                except threading.ThreadError: pass

            # re-raise the Exception
            raise


    def run_script(self):
        stdout, stderr = '', ''
        decoded_stdout, decoded_sterr = '', ''
        args = None
        script_outputs = {}

        try:
            # Get Docker arguments to execute the given script
            args = self.get_execution_arguments()
            if not args:
                raise SchedulerError('Not enough arguments for execution')
            self.log.debug(
                '[script %d] Container arguments: [ %s ]' % (
                self.script_id,
                ' '.join([str(x) for x in args])
            ))

            # Execute Docker command
            self.log.info(
                "[script %d] Running container (tick: %d, script type: %s, "
                "target IP: %s, target port: %d)" % (
                self.script_id,
                self.tick_id,
                self.script_type,
                self.ip,
                self.port
            ))

            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            self.log.info(
                "[script %d] Container run returned. (tick: %d, "
                "script type: %s, target IP: %s, target port: %d, self.status: %s)" % (
                self.script_id,
                self.tick_id,
                self.script_type,
                self.ip,
                self.port,
                self.get_status()
            ))

            # Check and decode output
            if stdout is None:
                raise SchedulerError('No output from the script')

            decoded_stdout = stdout.decode('utf-8').strip()
            decoded_stderr = stderr.decode('utf-8').strip()

            # Output of script is a JSON string
            try:
                self.result = json.loads(decoded_stdout)
            except ValueError:
                raise SchedulerError(
                    "Invalid output from the script. Arguments: {}, output: {}".format(
                    args, decoded_stdout)
                )

            if self.result['error']:
                self.result['error_msg'] += repr(
                    " | Script Object:" + self.get_status() +
                    " | Script output stdout:\n" + decoded_stdout +
                    "\n| stderr:\n" + decoded_stderr
                )

        except Exception as ex:

            if stderr is None:
                stderr = b''

            if isinstance(stderr, bytes):
                decoded_stderr = stderr.decode('utf-8').strip()

            if stdout is None:
                stdout = b''

            if isinstance(stdout, bytes):
                decoded_stdout = stdout.decode('utf-8').strip()

            self.result = {
                'error'     : ERROR_SCRIPT_EXECUTION[0],
                'error_msg' : ERROR_SCRIPT_EXECUTION[1] +
                             " Exception at ScriptExec.run(): " +
                             str(ex) +
                             str(traceback.format_exc()) +
                             " | script details: " + self.get_status() +
                             " | script output: stdout:\n" + decoded_stdout +
                             "\n | stderr:\n" + decoded_stderr
            }

            if not isinstance(ex, SchedulerError):
                self.log.error(
                    "An unexpected exception occurred in running sandbox: %s" %
                    self.result['error_msg']
                )

        # Push script results to DB
        try:
            script_outputs = str({
                'stdout': decoded_stdout[:self.max_output_send_bytes],
                'stderr': decoded_stderr[:self.max_output_send_bytes]
            })
            self.log.info(
                "[script %d] Tick %d, pushing result to remote side: %s | %s" % (
                self.script_id,
                self.tick_id,
                self.result,
                script_outputs
            ))
            self.push_result(self.result, script_outputs, args)
        except Exception as ex:
            self.log.error(
                "An unexpected exception occurred when updating service state: %s\n%s" % (
                str(ex),
                str(traceback.format_exc())
            ))


    def get_execution_arguments(self):
        arg_prefix = ['docker', 'run', '--rm']

        # The networking changes if we are running locally vs remotely
        if settings.IS_LOCAL_REGISTRY:
            # Use the DNS service provided by docker-compose
            arg_prefix += ['--network=container:docker_scriptbot{}_1'.format(settings.BOT_ID)]
        else:
            # Use the VPN when we run remotely
            arg_prefix += ['--network', 'host']

        arg_prefix += ['-e', 'TERM=linux', '-e', 'TERMINFO=/etc/terminfo']
        arg_prefix += [self.script_image_path]

        # PROPOSAL: prepend timeout --signal=SIGKILL str(self.timeout)
        # We want to use the host network so we have the correct address resolution for teams

        # Hard limit for a real kill
        arg_prefix += ['timeout', str(settings.SCRIPT_TIMEOUT_HARD)]

        # Soft limit so we can get a traceback
        arg_prefix += ['timeout', '-s', 'INT', str(settings.SCRIPT_TIMEOUT_SOFT)]

        arg_prefix += [self.script_name]
        arg_prefix += [self.ip, str(self.port)]

        # Script-type-specific args
        try:
            if self.script_type == 'benign':
                self.update_current_flag() # TODO: is it necessary?
                self.flag_meta['flag_id'] = ''
                self.flag_meta['secret_token'] = ''
                args = arg_prefix + [
                    "'%s'" % self.flag_meta['flag_id'],
                    "'%s'" % self.flag_meta['secret_token']
                ]

            elif self.script_type == 'exploit':
                if not self.update_current_flag():
                    raise ScriptExecError('No flag has been set for this service yet')

                if self.flag_meta['flag'] is None:
                    raise ScriptExecError('Could not get current flag from database.')

                if self.flag_meta['flag_id'] is None:
                    raise ScriptExecError('Could not get current flag_id from database.')

                args = arg_prefix + [
                    self.flag_meta['flag_id']
                ]

            elif self.script_type == 'setflag':
                self.log.info('Getting new flag for service %d' % self.service_id)

                self.flag_meta['flag_idx'], self.flag_meta['flag'] = \
                    self.db.generate_flag(self.team_id, self.service_id)

                args = arg_prefix + [
                    self.flag_meta['flag']
                ]

            elif self.script_type == 'getflag':
                if not self.update_current_flag():
                    raise ScriptExecError('No flag has been set for this service yet')

                if self.flag_meta['flag'] is None:
                    raise ScriptExecError('Could not get current flag from database.')

                if self.flag_meta['flag_id'] is None:
                    raise ScriptExecError('Could not get current flag_id from database.')

                args = arg_prefix + [
                    self.flag_meta['flag_id'],
                    self.flag_meta['secret_token']
                ]

            else:
                raise ScriptExecError('Unsupported script type "%s"' % self.script_type)

        except ScriptExecError as ex:
            self.result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': ERROR_SCRIPT_EXECUTION[1] +
                            " | An expected exception occurred in ScriptExec.get_execution_arguments(): " +
                            str(ex) +
                            " | script details: " + self.get_status()
            }
            self.log.warning(self.result['error_msg'])
            args = None

        except Exception as ex:
            error_msg = ERROR_SCRIPT_EXECUTION[1] + \
                  " | An unexpected exception occurred in ScriptExec.get_execution_arguments(): " + \
                  str(ex) + \
                  str(traceback.format_exc()) + \
                  ' | script details: ' + self.get_status()
            self.log.error(error_msg)
            self.result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': error_msg
            }

            args = None

        return args


    def update_current_flag(self):
        self.log.info('Getting current flag info for service %d' % self.service_id)

        flag, flag_id, secret_token = self.db.get_current_flag(self.team_id, self.service_id)

        self.flag_meta['flag'] = flag
        self.flag_meta['flag_id'] = flag_id
        self.flag_meta['secret_token'] = secret_token

        self.log.info(
            'New flag: %s (flag ID: %s, secret_token %s, team ID: %d, service ID: %d)' % (
            flag,
            flag_id,
            secret_token,
            self.team_id,
            self.service_id
        ))

        if flag is None:
            self.log.warning(
                "Service %d of team %d does not have a flag available" % (
                self.service_id,
                self.team_id
            ))
            return False
        return True


    def push_result(self, result, output, execution_args):
        try:
            payload = result.get('payload', {})
            if result['error'] == 0:
                if self.script_type == 'setflag':
                    if 'flag_id' not in payload or 'secret_token' not in payload:
                        self.log.error('"flag_id" or "secret_token" is missing. WTF. %r' % result)

                    else:
                        self.db.set_secret_token(self.flag_meta['flag_idx'], payload['flag_id'], payload['secret_token'])

                elif self.script_type == 'getflag':
                    if 'flag' not in payload:
                        result['error'] = ERROR_MISSING_FLAG[0]
                        result['error_msg'] = ERROR_MISSING_FLAG[1]

                    elif self.flag_meta['flag'] is not None:
                        if self.flag_meta['flag'] != payload['flag']:
                            # Incorrect flag
                            error_message = \
                                ('[script %d] getflag received an incorrect flag:' +
                                 'expected_flag:%s returned_flag:%s') % (
                                    self.script_id,
                                    self.flag_meta['flag'],
                                    str(payload['flag'])
                                )
                            result['error'] = ERROR_WRONG_FLAG[0]
                            result['error_msg'] = ERROR_WRONG_FLAG[1] + error_message

                elif self.script_type == 'exploit':
                    # Useful for admins to test
                    if 'flag' not in result:
                        result['error'] = ERROR_MISSING_FLAG[0]
                        result['error_msg'] = ERROR_MISSING_FLAG[1]

                    elif self.flag_meta['flag'] is not None:
                        if self.flag_meta['flag'] != payload['flag']:
                            # Incorrect flag
                            error_message = \
                                ('[script %d] exploit received an incorrect flag:' +
                                 'expected_flag:%s returned_flag:%s') % (
                                    self.script_id,
                                    self.flag_meta['flag'],
                                    str(payload['flag'])
                                )
                            result['error'] = ERROR_WRONG_FLAG[0]
                            result['error_msg'] = ERROR_WRONG_FLAG[1] + error_message

        except Exception as ex:
            self.log.error(
                'An unexpected exception occurred in push_result(): %s\n%s' % (
                str(ex),
                str(traceback.format_exc())
            ))
            result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': ERROR_SCRIPT_EXECUTION[1] + \
                             " Exception at ScriptExec.push_result(): " + \
                             str(ex) + \
                             ' | script details: ' + self.get_status()
            }

        self.result = result

        if self.result['error'] != 0:
            msg_prefix = '{{service: %s, type: %s, script_id: %d, ip: %s, port: %d, args: %s}}' % (
                self.service_name, self.script_type, self.script_id, self.ip, self.port, execution_args
            )
            self.log.warning("%s %s" % (msg_prefix, result['error_msg']))

        else:
            if self.script_type == 'setflag':
                self.log.info("SETFLAG TEAM %s:%d: (flag_id: %s, secret_token: %s) correctly set for service %s" % (
                 self.ip, self.port, payload['flag_id'], payload['secret_token'], self.service_name))
            elif self.script_type == 'getflag':
                self.log.info("GETFLAG TEAM %s:%d: (flag_id: %s, secret_token: %s, flag: %s) correctly set for service %s" % (
                 self.ip, self.port, self.flag_meta['flag_id'], self.flag_meta['secret_token'], payload['flag'], self.service_name))
            else:
                pass

        # Push the result to database
        self.db.push_result(self.execution_id, result, output)
