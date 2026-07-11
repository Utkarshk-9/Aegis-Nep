#PHASE 3: Stochastic Systems modeling
import numpy as np

# HARDWARE REFERRENCE PARAMETERS (NASA AEPS CEILING SPECS)
v_nominal = np.float32(600.0)  #Operating discharge voltage ceiling (Volts)
i_max_beam_amps = np.float32(25.0)  #Peak Hall-effect bea current threshold (Amps)
r_internal_ohms = np.float32(0.12)  #InternalPPU Tracking circuit resistance (Ohms)
thermal_capacitance = np.float32(180.0) #Material mass thermal score (Joule/kelvin)
weibull_beta_shape = np.float32(2.8) #Material degradation wear acceleration slope
weibull_eta_steps = np.float32(36500.0) # Component life rating scale (10x mission lifetime)

#Physics Constants
valve_resonance_omega = np.float32(0.05) #Fluid flow oscillation angular velocity tracking freaquency
cathode_poisoning_lambda = np.float32(4.0e-5) #Chemical contamination exponential accumulation decay rate
cathode_throttle_scaling = 0.5
#Deep-Space Therodynamic Upgrades
sigma_area = np.float32(1.5e-9)  #Commbined Emissivity * Stefan-Boltzman * Radiator Area
space_temp_k = np.float32(3.0)  # Background temperature of deep space (Kelvin)

class StochasticFailureEngine:
    def __init__(self):
        #Tracking component degradation across long-duration flight steps
        self.grid_age_steps = 0.0 
        self.damage_accumulation  = 0.0 
        self.ppu_temp_kelvin = 293.15 #Starts at ambient garage temp (20 degree celcius)
        self.grid_health_coef = 1.0 #Pristine Baseline Profile
        self.valve_flutter = 0.0 #Active Fluid Flow instability score (psi)
        self.cathode_poisoning = 0.0 #Active Chemical contamination score(chi)
        self.fault_state = 0 #State 0: Nominal Operation Loop

    def evaluate_step_physics(self, throttle_input, current_voltage, dt_seconds=1.0):
        """ROOM 3 MATH CORE: UPDATING ALL CROSS COUPLED DEGRADATION CHANNELS PER STEP"""
        #Advace engine component clock
        self.grid_age_steps +=1

        #Deriving beam current from agent's continuous throttle action
        active_beam_current = throttle_input * i_max_beam_amps

        #Thermodyanmic Coupling Engine (RK4 numerial integrator)
        joule_heating_watts = (active_beam_current **2) * r_internal_ohms #(i^2r)

        #Deifing non-linear derivaitve : dT/dt = (Q_in - Q_out) / C
        def get_temperature_derivative(current_temp):
            #Q_out calculated via Stefan-Boltzmann Law (T^4)
            radiative_cooling_watts = sigma_area * (np.power(current_temp, 4) - np.power(space_temp_k,4))
            return float((joule_heating_watts - radiative_cooling_watts) / thermal_capacitance)
            
        #Computing RK4 evaluation coeffcients across dt inerval
        t_curr = self.ppu_temp_kelvin
        k1 = get_temperature_derivative(t_curr)
        k2 = get_temperature_derivative(t_curr + 0.5 * dt_seconds * k1)
        k3 = get_temperature_derivative(t_curr + 0.5 * dt_seconds * k2)
        k4 = get_temperature_derivative(t_curr + dt_seconds * k3)

        #Updating system state by weight average slope of all 4 steps
        self.ppu_temp_kelvin += (dt_seconds / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

        #Ion sputtering and damage accumulation block
        #Corrected per-second phyics clock to avoid mathematical supression
        time_ratio = self.grid_age_steps / weibull_eta_steps
        weibull_hazard = (weibull_beta_shape/ weibull_eta_steps) * (time_ratio ** (weibull_beta_shape - 1.0))
        step_damage = weibull_hazard * (dt_seconds / 86400.0) * (1.0 + throttle_input)
        self.damage_accumulation += float(step_damage)
        self.grid_health_coef = float(np.exp(-self.damage_accumulation))

        #Reliability Probability Calculation (Weibull Cumulative Risk Profile)
        reliability_probability = 1.0 - np.exp(-(time_ratio ** weibull_beta_shape))

        #Stochastic Degradation Loops 
        #Mechanical Xenon Valve Flutter (Sinusodial Fluid Transient Flow Wave)
        if throttle_input > 0.0:
            #Valve flutter scales with throttle magnitude and worsen as grid health decays
            oscillation_wave = np.sin(valve_resonance_omega * self.grid_age_steps)
            self.valve_flutter = float(throttle_input *abs(oscillation_wave) * (1.0 - self.grid_health_coef))
        else:
            self.valve_flutter = 0.0

        #Chemical Cathode Poisoning Emitter(Exponential Chemical Decay)
        #Contammination piles up during operational steps over flight hours
        if throttle_input > 0.0:
            contamination_time = self.grid_age_steps * (dt_seconds / 3600.0)
            throttle_factor = cathode_throttle_scalling + 1.0 * throttle_input
            self.cathode_poisoning = np.float32(1.0 - np.exp(-cathode_poisoning_lambda * contamination_time * throttle_factor))

        #Paschen Coupling and Thermal Arc flash event checks
        #Arc Threshold collapses violenlty as grid wear, valve flutter, and temperature spike
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
            self.fault_state = 3 #State 3: Critical
            updated_voltage = current_voltage * 0.85
        elif system_health_score < 0.70:
            self.fault_state = 2 #Degraded
            updated_voltage = current_voltage
        elif system_health_score < 0.90:
            self.fault_state = 1 #State 1: Warning
            updated_voltage = current_voltage
        else:
            self.fault_state = 0 #Nominal Operations
            updated_voltage = current_voltage

        return (float(self.grid_health_coef),
                float(reliability_probability),
                float(self.ppu_temp_kelvin),
                float(self.valve_flutter),
                float(self.cathode_poisoning),
                float(updated_voltage),
                int(self.fault_state))



 


