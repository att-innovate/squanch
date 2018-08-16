import numpy as np

from squanch import gates

__all__ = ["QError", "AttenuationError", "RandomUnitaryError", "SystematicUnitaryError"]


class QError:
    '''A generalized quantum error model'''

    def __init__(self, qchannel):
        '''
        Base initialization class; extend in child methods by overwriting along with QError.__init__(self, qchannel)

        :param qchannel: the quantum channel this error model is being used on
        '''
        self.qchannel = qchannel

    def apply(self, qubit):
        '''
        Applies the error to the transmitted qubit. Overwrite this method in child classes while maintaining the
        Qubit->(Qubit | None) signature

        :param Qubit qubit: the qubit being withdrawn from the quantum channel with channel.get(); possibly None
        :return: the modified qubit
        '''
        if qubit is not None:
            # Implement error logic here
            pass
        return qubit


class AttenuationError(QError):
    '''Simulate the possible loss of a qubit in a fiber optic channel due to attenuation effects'''

    def __init__(self, qchannel, attenuation_coefficient = -0.16):
        '''
        Instatiate the error class

        :param QChannel qchannel: parent quantum channel
        :param float attenuation_coefficient: attenuation of fiber in dB/km; default: -.16 dB/km, from Yin, et al
        '''
        QError.__init__(self, qchannel)
        decibel_loss = qchannel.length * attenuation_coefficient
        self.attenuation = 10 ** (decibel_loss / 10)  # Total attenuation along the fiber

    def apply(self, qubit):
        '''
        Simulates possible loss + measurement of qubit

        :param Qubit qubit: qubit from quantum channel
        :return: either unchanged qubit or None
        '''
        if np.random.rand() > self.attenuation and qubit is not None:
            # Photon was lost due to attenuation effects; collapse state and return nothing
            qubit.measure()
            qubit = None
        return qubit


class RandomUnitaryError(QError):
    '''Simualates a random rotation along X and Z with a Gaussian distribution of rotation angles'''

    def __init__(self, qchannel, variance):
        '''
        Instatiate the error class

        :param QChannel qchannel: parent quantum channel
        :param float variance: variance to use in the Gaussian sampling of X and Z rotation angles
        '''
        QError.__init__(self, qchannel)
        self.variance = variance

    def apply(self, qubit):
        '''
        Simulates random rotations on X and Z of a qubit

        :param Qubit qubit: qubit from quantum channel
        :return: rotated qubit
        '''
        if qubit is not None:
            x_angle, z_angle = np.random.normal(0, self.variance, 2)
            gates.RX(qubit, x_angle)
            gates.RZ(qubit, z_angle)
        return qubit


class SystematicUnitaryError(QError):
    '''Simulates a random unitary error that is the same for each qubit'''

    def __init__(self, qchannel, operator = None, variance = None):
        '''
        Instantiate the systematic unitary error class

        :param QChannel qchannel: parent quantum channel
        :param np.array operator:
        :param float variance:
        '''
        QError.__init__(self, qchannel)
        assert operator is not None or variance is not None, \
            "Provide either a random operator or a variance value to use for sampling."

        if operator is not None:
            self.operator = operator
        elif variance is not None:
            x_angle, z_angle = np.random.normal(0, variance, 2)
            Rx = np.cos(x_angle / 2.0) * gates._I - 1j * np.sin(x_angle / 2.0) * gates._X
            Rz = np.cos(z_angle / 2.0) * gates._I - 1j * np.sin(z_angle / 2.0) * gates._Z
            self.operator = np.dot(Rz, Rx)

    def apply(self, qubit):
        '''
        Simulates the application of the unitary error

        :param Qubit qubit: qubit from quantum channel
        :return: rotated qubit
        '''
        if qubit is not None:
            qubit.qsystem.apply(self.operator)
        return qubit
