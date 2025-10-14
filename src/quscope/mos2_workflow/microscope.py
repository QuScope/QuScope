from dataclasses import dataclass


@dataclass
class MicroscopeParams:
    acceleration_voltage: float = 200e3  # Volts
    defocus: float = 200.0  # Angstroms
    cs: float = 1.0  # mm
    astigmatism: float = 0.0
    aperture: float = 50.0  # mrad

    def to_abtem_kwargs(self):
        return {
            'energy': self.acceleration_voltage,
            'defocus': self.defocus,
            'cs': self.cs,
            'aperture': self.aperture
        }
