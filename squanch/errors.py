import numpy as np
import gates


class QError:
    '''A generalized error model'''

    def __init__(self, qchannel):
        '''
        Base initialization class; extend in child methods by overwriting along with QError.__init__(self, qchannel)

        :param qchannel: the quantum channel this error model is being used on
        '''
        self.qchannel = qchannel

    def apply(self, qubit):
        '''
        Generic apply method; overwrite in child methods while maintaining the Qubit->(Qubit | None) signature

        :param Qubit qubit: the qubit being withdrawn from the quantum channel with channel.get(); possibly None
        :return: the modified qubit
        '''
        if qubit is not None:
            # Implement error logic here
            pass
        return qubit


class AttenuationError(QError):
    '''Simulate the possible loss of a qubit in a fiber optic channel due to attenuation effects'''

    def __init__(self, qchannel, attenuationCoefficient = -0.16):
        '''
        Instatiate the error class

        :param QChannel qchannel: parent quantum channel
        :param float attenuationCoefficient: attenuation of fiber in dB/km; default: -.16 dB/km, from Yin, et al
        '''
        QError.__init__(self, qchannel)
        decibelLoss = qchannel.length * attenuationCoefficient
        self.attenuation = 10 ** (decibelLoss / 10)  # Total attenuation along the fiber

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

    def __init__(self, qchannel, randomUnitarySigma):
        '''
        Instatiate the error class

        :param QChannel qchannel: parent quantum channel
        :param float randomUnitarySigma: sigma to use in the Gaussian sampling of X and Z rotation angles
        '''
        QError.__init__(self, qchannel)
        self.sigma = randomUnitarySigma

    def apply(self, qubit):
        '''
        Simulates random rotations on X and Z of a qubit

        :param Qubit qubit: qubit from quantum channel
        :return: rotated qubit
        '''
        if qubit is not None:
            xAngle, zAngle = np.random.normal(0, self.sigma, 2)
            gates.RX(qubit, xAngle)
            gates.RZ(qubit, zAngle)
        return qubit


class SystematicUnitaryError(QError):
    '''Simulates a random unitary error that is the same for each qubit'''

    def __init__(self, qchannel, unitaryOperation = None, randomUnitarySigma = None):
        '''
        Instantiate the systematic unitary error class

        :param QChannel qchannel: parent quantum channel
        :param np.array unitaryOperation:
        :param float randomUnitarySigma:
        '''
        QError.__init__(self, qchannel)
        assert unitaryOperation is not None or randomUnitarySigma is not None, \
            "Provide either a random operator or a sigma value to use for sampling."

        if unitaryOperation is not None:
            self.operator = unitaryOperation
        elif randomUnitarySigma is not None:
            xAngle, zAngle = np.random.normal(0, randomUnitarySigma, 2)
            Rx = np.cos(xAngle / 2.0) * gates._I - 1j * np.sin(xAngle / 2.0) * gates._X
            Rz = np.cos(zAngle / 2.0) * gates._I - 1j * np.sin(zAngle / 2.0) * gates._Z
            self.operator = np.dot(Rz, Rx)

    def apply(self, qubit):
        '''
        Simulates the application of the unitary error

        :param Qubit qubit: qubit from quantum channel
        :return: rotated qubit
        '''
        if qubit is not None:
            qubit.qSystem.apply(self.operator)
        return qubit
