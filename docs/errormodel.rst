.. hydra documentation master file, created by
   sphinx-quickstart on Thu Jan 28 14:55:49 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Error model
=================================

**************
Heating errors
**************

Infidelities due to heating are fortunately straightforward and analytically derived in the original MS paper. The error
equation is 

.. math::
	\epsilon_H = 1- \frac{1}{8}(3 + 4 e^{-\frac{\dot{n}\pi}{2\sqrt{q}\eta\Omega}} + e^{-\frac{2\dot{n}\pi}{\sqrt{q}\eta\Omega}}).

Here, the heating rate in quanta/s is :math:`\dot{n}`, :math:`\eta` is the Lamb-Dicke parameter, :math:`\Omega` the MS sideband fields' power and :math:`q` the
number of loops completed in phase space (we usually set :math:`q=1`).

Heating of a vibrational mode is caused my electric field matching the frequency of said mode. For a chain of 2 ions, there are 2 modes of motion: the center-of-mass (COM)
mode which describes in phase motion, and the stretch (STR) mode which is out of phase. Recall that the mode's frequencies are related by 
:math:`\nu_{S} = \sqrt{3}\nu_{C}`. The heating rates are found to be :

.. math::
	\dot{n}_c(\nu_c) = \frac{e^2}{4m\hbar\nu_c}S_E(\nu_c)
	
	\dot{n}_s(\nu_s) = \frac{e^2}{4m\hbar\nu_c}\frac{S_E(\nu_s)}{d^2}\Delta x^2
	
The ion's spatial extent is :math:`\Delta x = (\frac{3e^2}{2\pi \epsilon_0 m})^{1/3}`, and we've introduced :math:`d` as the ion-chip distance. We first note that 
:math:`\dot{n}_c > \dot{n}_s`, i.e. heating the STR mode is more difficult. This makes sense as heating the STR mode involves exciting out of phase motion, hence it is the
gradient of the electric field at the ion's position that matters, and not the magnitude of the electric field itself. The second note is that the Power Spectral 
Density (PSD) of the Electric field noise generally scales as 1/f. It is therefore generally advantageous to increase the secular frequency as
the noise will decrease. This also explains why the STR heating rate is generally lower, as :math:`\nu_s > \nu_c`.

When comparing heating rates in the literature, it is more useful to compare the scaled Electric field density :math:`\nu_c S_E(\nu_c)`, which is a constant if 
the noise PSD is indeed of the form :math:`S_E(\omega) = A/\omega`. Therefore, one can vary the scaled E-field density in Hydra as opposed to the heating rate. 

***********
Decoherence
***********

Decoherence arises from depolarization and dephasing, however we'll ignore depolarization as it is neglibile for ytterbium. Dephasing arises form magnetic
field noise which fluctuates the energy levels of the qubit. Since the energy splitting changes the phase relationship of the qubit, fluctuations of the former will add 
uncertainty to the phase, hence the term dephasing. 

The qubit itself can be thought of as a filter. When left to its own devices, the qubit acts as a low pass filter, where for an evolution time :math:`\tau`, noise at 
frequencies :math:`0 < \omega < 2\pi/\tau` will cause dephasing. In other cases however, the qubit can be engineered to act as a narrow passband filter, where only noise
at a certain frequency will be detrimental. We approach the idea of filter functions : under any experimental sequence, there exists a filter function of the qubit which 
convolutes with the PSD. We can therefore appreciate the difficulty in estimating errors due to decoherence as they largely depend on the exact shape of the PSD and 
the specific gate scheme. We'll nevertheless try and provide a general error function. The generalized decay due to dephasing is 

.. math::
	\chi(t) = \exp (-\int_0^\infty \frac{d\omega}{\pi} S(\omega) \frac{F(\omega t)}{\omega^2}).
	
where the filter function is represented by :math:`F(\omega t)`. Note that the filter function is normalized such that

.. math::
	\int^{+\infty}_{-\infty} \frac{d\omega}{\pi}\frac{F(\omega t)}{\omega^2} = \tau.
	
This should therefore make it obvious as to why dynamical decoupling schemes are rendered useless in front of a broadband white noise spectrum, i.e. :math:`S(\omega) = cst`.
That is because the filter function is normalized, and the noise is equal for every frequency, hence any type of filter function will return the same noise. 

We can now try and adapt this theory to our error model. We stipulate that there exists an optimal filter function assuming the perfect knowledge of the noise sources' PSD.
The perfect filter function would look like a delta function that would sample the PSD's frequency with the lowest noise, and the function would become

.. math::
	F(\omega t) = \pi \delta(\omega_0 - |\omega|) \omega^2 t/2

Plugging this back into the decay error function, 

.. math::
	\epsilon_D = 1 - \exp (-\frac{t}{2}S(\omega_0))
	
It turns out that the various gate schemes under consideration all use DD protocols with filter function that can be likened to a delta function within good approximation. 
Keep in mind that the decay function provided does not reflect the true fidelity of an entangling gate, but provides a very reasonable estimate. With this final error function,
we can compute the fidelity given a noise S(\omega_0). This value must be interpreted as follows: what is the smallest achievable noise of the magnetic field's PSD within
an acceptable frequency range? The frequency range is determined by hardware limits, and is generally :math:`\omega/2\pi \in [10, 50]` kHz.


**********************************
Vibrational frequency fluctuations
**********************************

The vibrational frequency of the ion :math:`\nu` may fluctuate for various reasons, two of which are discussed here : Kerr coupling and voltage noise. In order to perform
a perfect entangling gate, the sideband fields driving the entanglement must be slightly detuned from the motional frquency by an amount :math:`\delta_s = \nu - \nu_0`. 
Fluctuations of the trap frequency :math:`\nu` will therefore induce noise in the detuning of the fields, which in turn will damage the fidelity. The error due to a misset
detuning :math:`\Delta\delta_s` is

.. math::
	\epsilon_s = \Delta\delta_s^2 \frac{\pi^2}{\eta^2\Omega^2} \frac{1+2q(1+2\bar{n})}{16 q}
	
In the case of a fluctuating detuning, we can replace the static offset :math:`\Delta\delta_s^2` with the variance of the noise, :math:`\sigma_{\delta_s}^2`. Noises arising from 
Kerr coupling and trapping voltages are uncorrelated, hence the total variance is the sum of both noise sources, :math:`\sigma^2_{tot} = \sigma_K^2 + \sigma_V^2`. 	

Kerr coupling is an effect which arises from the cross coupling of the vibrations: the radial rocking modes are intrinsically coupled to the axial STR mode. Note that
Kerr coupling errors therefore only arise when the gate is performed on the axial STR mode. The interaction strength is determined by the Kerr constant,

.. math::
	K = -\nu_s(\frac{1}{2} + \frac{\nu_s^2/2}{4\nu_r^2 - \nu_s^2})\frac{\nu_c}{\nu_r}(\frac{2\hbar\nu_c}{\alpha^2 m c^2})^{1/3}.

where :math:`\nu_s` is the axial STR frequency, :math:`\nu_r` the radial rocking frequency, :math:`\nu_c` the axial COM frequency and :math:`\alpha` 
the fine structure constant. The variance of the axial STR frequency due to Kerr coupling is therefore found to be

.. math::
	\sigma_K^2 =  K^2 \bar{n}_r (2 \bar{n}_r + 1)
	
where :math:`\bar{n}_r` is the temperature of the radial rocking mode, which is determined from the Doppler cooling limit. 

Fluctuations from voltage noise are harder to model as they strongly depend on the geometry of the electrodes and the PSD of the voltage noise. This parameter is therefore
kept as :math:`\sigma_V^2` and can be set in Hydra.
	

*********************
Off-resonant coupling
*********************

The sideband fields may couple to the carrier and induce errors. The off-resonant interaction causes small oscillations of the population.
The infidelities are estimated to be 

.. math::
	\epsilon_o = \frac{\Omega^2}{\nu^2}
	
The frequency :math:`\nu` depends on which vibrational mode is used. For typicaly experimental parameters, the error becomes quickly appreciable. We can use 
amplitude pulse shaping to reduce the infidelity. The error then becomes : 

COMING SOON...


**********************
Amplitude fluctuations
**********************

In certain dynamical decoupling schemes, noise from dephasing is reduced by continuously driving the carrier transition. This results in a delta like filter function
whose frequency is that of the drive's power. Noise in the dynamical decoupling drive's amplitude will eventually cause decoherence in the same way that magnetic 
fluctuations lead to dephasing. We estimate the associated infidelity by considering a simpler case, evaluating the errors due to amplitude noise during a rabi oscillation.
Fortunately, the decay function is very similar to the filter function formalism described previously. The noise process under consideration however is now :math:`S_\Omega(\omega)`,
the PSD of rabi frequency noise. The noise spectrum has been well characterized and is modelled as 

.. math::
	S_\Omega(\omega) = (2 \pi)^2 \frac{S_0}{\omega_0^2 + \omega^2}

This describes a white noise spectrum of to :math:`\omega_0` followed by a :math:`1/\omega^2` decay. The cutoff frequency was found to be :math:`\omega_0/2\pi = 3` kHz. 
When speaking of amplitude noise however, it is often more conveniant to compare the Signal to Noise Ratio (SNR), i.e. the relative fluctuations :math:`\delta\Omega/\Omega`. 
The exact noise spectrum can then be worked out from the SNR.

We end up with an error function quite similar to the decoherence one,

COMING SOON...












	