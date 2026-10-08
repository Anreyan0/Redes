class CongestionControl:

    def __init__(self, MSS: int):

        # STATE 0 = SLOW START | STATE 1 = CONGESTION AVOIDANCE
        self.current_state = 0
        # MSS
        self.MSS = MSS
        # cwnd = 1 MSS
        self.cwnd = MSS
        # ssthresh 
        # Cuando STATE = 0 (SLOW START), si cwnd >= ssthresh --> STATE = 1 (CONGESTION AVOIDANCE)
        # Se define luego del primer timeout durante slow start. Inicialmente None
        self.ssthresh = None
        # is_first_timeout
        # True si aun no hay ningun timeout dentro del estado SLOW START. False en caso contrario
        self.is_first_timeout_ss = True

    def get_cwnd(self) -> bytes:
        return self.cwnd

    def get_MSS_in_cwnd(self) -> int:
        return self.cwnd // self.MSS

    def event_ack_received(self):
        # SLOW START
        if self.current_state == 0:
            self.cwnd += self.MSS

            if (self.ssthresh is not None) and (self.cwnd >= self.ssthresh):
                self.current_state = 1
                self.is_first_timeout_ss = True
                
        # CONGESTION AVOIDANCE
        else:
            self.cwnd += (1 / self.get_MSS_in_cwnd()) * self.MSS

    def event_timeout(self):
        # SLOW START
        if self.current_state == 0:
            # Primer timeout dentro de SLOW START
            if self.is_first_timeout_ss == True:
                self.ssthresh = self.cwnd // 2
                self.cwnd = self.MSS
                self.is_first_timeout_ss = False

        # CONGESTION AVOIDANCE
        else:
            # Volvemos a SLOW START
            self.current_state = 0
            self.ssthresh = self.cwnd // 2
            self.cwnd = self.MSS

    def is_state_slow_start(self):
        return self.current_state == 0

    def is_state_congestion_avoidance(self):
        return self.current_state == 1

    def get_ssthresh(self):
        return self.ssthresh




    
    
