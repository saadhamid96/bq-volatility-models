"""Stochastic volatility models."""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from scipy.integrate import quad  # type: ignore[import-untyped]


class HestonParameters(NamedTuple):
    """Parameters for the Heston stochastic volatility model."""

    v0: float
    kappa: float
    theta: float
    sigma: float
    rho: float
    lambd: float


class HestonModel:
    """Heston stochastic volatility model."""

    def __init__(
        self,
        parameters: HestonParameters | None = None,
        risk_free_rate: float = 0.0,
    ) -> None:
        """Initialize the Heston model with parameters and risk-free rate."""
        self.parameters = parameters or HestonParameters(
            1.0,
            2.0,
            0.04,
            0.1,
            -0.5,
            0.04,
        )
        self.risk_free_rate = risk_free_rate

    @property
    def parameters(self) -> HestonParameters:
        """Get the model parameters."""
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: HestonParameters) -> None:
        """Set the model parameters."""
        self._parameters = parameters

    @property
    def risk_free_rate(self) -> float:
        """Get the risk-free rate."""
        return self._risk_free_rate

    @risk_free_rate.setter
    def risk_free_rate(self, risk_free_rate: float) -> None:
        """Set the risk-free rate."""
        self._risk_free_rate = risk_free_rate

    def characteristic_function(
        self,
        phi: complex,
        spot: float,
        maturity: float,
    ) -> complex:
        """Calculate the characteristic function of the Heston model.

        :param phi: The Fourier transform variable.
        :param spot: Current spot price of the underlying asset.
        :param maturity: Time to maturity in days.
        :return: The characteristic function value.
        """
        s0 = spot
        tau = maturity
        r = self.risk_free_rate
        v0 = self.parameters.v0
        kappa = self.parameters.kappa
        theta = self.parameters.theta
        sigma = self.parameters.sigma
        rho = self.parameters.rho
        lambd = self.parameters.lambd
        # constants
        a = kappa * theta
        b = kappa + lambd

        # common terms w.r.t phi
        rspi = rho * sigma * phi * 1j

        # define d parameter given phi and b
        d = np.sqrt((rho * sigma * phi * 1j - b) ** 2 + (phi * 1j + phi**2) * sigma**2)

        # define g parameter given phi, b and d
        g = (b - rspi + d) / (b - rspi - d)

        # calculate characteristic function by components
        exp1 = np.exp(r * phi * 1j * tau)
        term2 = s0 ** (phi * 1j) * ((1 - g * np.exp(d * tau)) / (1 - g)) ** (
            -2 * a / sigma**2
        )
        exp2 = np.exp(
            a * tau * (b - rspi + d) / sigma**2
            + v0
            * (b - rspi + d)
            * ((1 - np.exp(d * tau)) / (1 - g * np.exp(d * tau)))
            / sigma**2,
        )

        return exp1 * term2 * exp2  # type: ignore[no-any-return]

    def price(self, spot: float, strike: float, maturity: int) -> float:
        """Calculate the price of an option.

        :param spot: Current spot price of the underlying asset.
        :param strike: Strike price of the option.
        :param maturity: Time to maturity in days.
        :return: The option price.
        """

        def integrand(phi: complex) -> complex:
            """Integrand for the Fourier transform."""
            numerator = np.exp(
                self.risk_free_rate * maturity,
            ) * self.characteristic_function(
                phi - 1j,
                spot,
                maturity,
            ) - strike * self.characteristic_function(phi, spot, maturity)
            denominator = 1j * phi * strike ** (1j * phi)
            return numerator / denominator  # type: ignore[no-any-return]

        real_integral, err = np.real(quad(integrand, 0, 100))
        return (  # type: ignore[no-any-return]
            spot - strike * np.exp(-self.risk_free_rate * maturity)
        ) / 2 + real_integral / np.pi
