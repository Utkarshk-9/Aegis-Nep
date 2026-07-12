#PHASE 3: Stochastic Systems modeling
import numpy as np

# HARDWARE REFERRENCE PARAMETERS (NASA AEPS CEILING SPECS)
v_nominal = np.float32(600.0)  #Operating discharge voltage ceiling (Volts)
i_max_beam_amps = np.float32(25.0)  #Peak Hall-effect bea current threshold (Amps)
r_internal_ohms = np.float32(1.152)  #InternalPPU Tracking circuit resistance (Ohms)
thermal_capacitance = np.float32(150000.0) #Material mass thermal score (Joule/kelvin)
weibull_beta_shape = np.float32(2.8) #Material degradation wear acceleration slope
weibull_eta_steps = np.float32(1000.0) # Component life rating scale (10x mission lifetime)

#Physics Constants
valve_resonance_omega = np.float32(0.05) #Fluid flow oscillation angular velocity tracking freaquency
cathode_poisoning_lambda = np.float32(4.0e-5) #Chemical contamination exponential accumulation decay rate
cathode_throttle_scaling = 0.5
#Deep-Space Therodynamic Upgrades
sigma_area = np.float32(5.67e-8 * 0.85 * 40.5 * 0.0004)  #Commbined Emissivity * Stefan-Boltzman * Radiator Area * Bay Insulation Shunt (Evaluates to - 7.23e-10)
space_temp_k = np.float32(3.0)  # Background temperature of deep space (Kelvin)

#RK4 sub_stepping
max_stable_substep_sec = 30.0

class StochasticFailureEngine:
    def __init__(self):
        #Tracking component degradation across long-duration flight steps
        self.cumulative_flight_seconds = 0.0
        self.grid_age_steps = 0.0 
        self.damage_accumulation  = 0.0 
        self.ppu_temp_kelvin = 293.15 #Starts at ambient garage temp (20 degrees celcius)
        self.grid_health_coef = 1.0 #Pristine Baseline Profile
        self.valve_flutter = 0.0 #Active Fluid Flow instability score (psi)
        self.cathode_poisoning = 0.0 #Active Chemical contamination score(chi)
        self.fault_state = 0 #State 0: Nominal Operation Loop

    def evaluate_step_physics(self, throttle_input, current_voltage, dt_seconds=1.0):
        """ROOM 3 MATH CORE: UPDATING ALL CROSS-COUPLED DEGRADATION CHANNELS PER STEP"""
        #Advance engine component clock
        self.cumulative_flight_seconds += dt_seconds
        
        #Deriving beam current from agent's continuous throttle action
        active_beam_current = throttle_input * i_max_beam_amps

        #Thermodyanmic Coupling Engine (RK4 numerial integrator)
        joule_heating_watts = (active_beam_current **2) * r_internal_ohms #(i^2r)
        
        #740W from PPU + 50,000W background heat from nuclear reactor 
        total_heat_in_watts = joule_heating_watts + 50000.0

        #Defining non-linear derivative : dT/dt = (Q_in - Q_out) / C
        def get_temperature_derivative(current_temp):
            #Q_out calculated via Stefan-Boltzmann Law (T^4)
            radiative_cooling_watts = sigma_area * (np.power(current_temp, 4) - np.power(space_temp_k,4))
            return float((total_heat_in_watts - radiative_cooling_watts) / thermal_capacitance)
            
        #Splitting dr_seconds into small enough  sub_steps for RK4 to say stable
        n_substep = max(1, int(np.ceil(dt_seconds / max_stable_substep_sec)))
        sub_dt = dt_seconds / n_substep
        for _ in range(n_substep):
         #Splitting dt_seconds into small enough sub_step for RK4 to stay stable
         #Computing RK4 evaluation coefficients across dt inerval
         t_curr = self.ppu_temp_kelvin
         k1 = get_temperature_derivative(t_curr)
         k2 = get_temperature_derivative(t_curr + 0.5 * sub_dt * k1)
         k3 = get_temperature_derivative(t_curr + 0.5 * sub_dt * k2)
         k4 = get_temperature_derivative(t_curr + sub_dt * k3)

        #Updating system state by weight average slope of all 4 steps
         self.ppu_temp_kelvin += (sub_dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

        #Weibull accumulation (matching frequency)
        weibull_eta_seconds = weibull_eta_steps * 86400.0
        time_ratio = self.cumulative_flight_seconds / weibull_eta_seconds

        #Calculating instantaneous hazard rate based on time elapsed
        if time_ratio > 0.0:
            weibull_hazard = (weibull_beta_shape / weibull_eta_seconds) * (time_ratio ** (weibull_beta_shape - 1.0))
        else:
            weibull_hazard = 0.0
        #Ion sputtering and damage accumulation block
        step_damage = weibull_hazard * dt_seconds* (1.0 + throttle_input)
        self.damage_accumulation += float(step_damage)
        self.grid_health_coef = float(np.exp(-self.damage_accumulation))

        #Reliability Probability Calculation (Weibull Cumulative Risk Profile)
        reliability_probability = 1.0 - np.exp(-(time_ratio ** weibull_beta_shape)) if time_ratio >= 0.0 else 0.0

        #Stochastic Degradation Loops 
        #Mechanical Xenon Valve Flutter (Sinusoidal Fluid Transient Flow Wave)
        if throttle_input > 0.0:
            #Valve flutter scales with throttle magnitude and worsen as grid health decays
            oscillation_wave = np.sin(valve_resonance_omega * self.cumulative_flight_seconds)
            self.valve_flutter = float(throttle_input *abs(oscillation_wave) * (1.0 - self.grid_health_coef))
        else:
            self.valve_flutter = 0.0

        #Chemical Cathode Poisoning Emitter(Exponential Chemical Decay)
        #Contamination piles up during operational steps over flight hours
        if throttle_input > 0.0:
            contamination_time = self.cumulative_flight_seconds / 3600.0
            throttle_factor = cathode_throttle_scaling + 1.0 * throttle_input
            self.cathode_poisoning = float(1.0 - np.exp(-cathode_poisoning_lambda * contamination_time * throttle_factor))

        #Paschen Coupling and Thermal Arc flash event checks
        #Arc Threshold collapses violently as grid wear, valve flutter, and temperature spike
        cross_coupled_wear = self.grid_health_coef * (1.0 - 0.2 * self.valve_flutter) * (1.0 - 0.3 * self.cathode_poisoning)
        arc_breakdown_threshold_volts = 1000.0 * cross_coupled_wear * (300.0 / self.ppu_temp_kelvin)
        arc_triggered = current_voltage > arc_breakdown_threshold_volts

        #5-STATE MULTI-PHYSICS HEALTH STATE MACHINE ASSIGNMENTS
        #Factor in alpha wear, valve flutters, and cathode contamination simultaneously
        total_degradation = (0.5 * ( 1.0 - self.grid_health_coef)) + (0.3 * self.cathode_poisoning) + (0.2 * self.valve_flutter)
        system_health_score = max(0.0,1.0 - total_degradation)

        if arc_triggered or system_health_score <= 0.05:
            self.fault_state = 4 #State4: Catastrophic Faliure
            updated_voltage = 0.0 #Circuit breakers trip instantly - voltage dropped to 0
            self.grid_health_coef = 0.0
        elif system_health_score < 0.40 or self.ppu_temp_kelvin > 423.15:
            self.fault_state = 3 
            #State 3: Scalling Down from the absolute nominal ceiling 
            updated_voltage = float(v_nominal * 0.85)
        elif system_health_score < 0.70:
            self.fault_state = 2 #Degraded
            updated_voltage = float(v_nominal)
        elif system_health_score < 0.90:
            self.fault_state = 1 #State 1: Warning
            updated_voltage = float(v_nominal)
        else:
            self.fault_state = 0 #Nominal Operations
            updated_voltage = float(v_nominal)

        return (float(self.grid_health_coef),
                float(reliability_probability),
                float(self.ppu_temp_kelvin),
                float(self.valve_flutter),
                float(self.cathode_poisoning),
                float(updated_voltage),
                int(self.fault_state))


#PHASE 3 DONE---


 


