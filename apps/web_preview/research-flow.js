export const ResearchContinuation = Object.freeze({
  DEVELOPER_DOSSIER: 'DEVELOPER_DOSSIER',
  SIMULATED_PAYWALL: 'SIMULATED_PAYWALL',
});

export function useDemoPrecheck({developerMode, simulateUserPaywall, identifier,
  sampleVin, market, identifierType}) {
  return !(developerMode && !simulateUserPaywall)
    && identifier === sampleVin && market === 'USA' && identifierType === 'VIN';
}

export function selectResearchContinuation({developerMode, simulateUserPaywall}) {
  return developerMode && !simulateUserPaywall
    ? ResearchContinuation.DEVELOPER_DOSSIER
    : ResearchContinuation.SIMULATED_PAYWALL;
}

export function researchContinuationRequest({
  developerMode,
  simulateUserPaywall,
  jobId,
  profileId,
  language,
  vin = '',
}) {
  const mode = selectResearchContinuation({developerMode, simulateUserPaywall});
  if (mode === ResearchContinuation.DEVELOPER_DOSSIER) {
    return {
      mode,
      path: `/research/jobs/${jobId}/developer-dossier`,
      options: {method: 'POST'},
    };
  }
  return {
    mode,
    path: `/vin/profiles/${profileId}/demo-precheck`,
    options: {
      method: 'POST',
      body: JSON.stringify({language, vin: vin || null}),
    },
  };
}

export async function executeResearchContinuation(apiCall, values) {
  const request = researchContinuationRequest(values);
  const result = await apiCall(request.path, request.options);
  return {mode: request.mode, result};
}
