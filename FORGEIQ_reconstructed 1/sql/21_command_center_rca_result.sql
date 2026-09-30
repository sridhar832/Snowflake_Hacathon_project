CREATE OR REPLACE TABLE FORGEIQ.ANALYTICS.COMMAND_CENTER_RCA_RESULTS AS
SELECT
    ASSET_ID,EVENT_TIMESTAMP,FAILURE_PROBABILITY,RISK_LEVEL,
    LIKELY_FAILURE_TYPE,RECOMMENDED_ACTION,OEE,
    REPLACE(
      AI_COMPLETE('llama3.1-70b',
        CONCAT(
          'You are an industrial predictive maintenance assistant. ',
          'Analyze the equipment condition below. ',
          'Explain why the equipment is at risk using ONLY the supplied data. ',
          'Do not invent measurements or events. Do not claim certainty. ',
          'Write a concise explanation for a maintenance engineer. ',
          'Include: 1) strongest sensor indicators, 2) maintenance context, ',
          '3) likely failure mode, 4) recommended action. ',
          '\n\nAsset: ',ASSET_ID,
          '\nFailure probability: ',ROUND(FAILURE_PROBABILITY*100,1),'%',
          '\nRisk level: ',RISK_LEVEL,
          '\nLikely failure type: ',LIKELY_FAILURE_TYPE,
          '\nAverage vibration: ',ROUND(AVG_VIBRATION,2),' mm/s',
          '\nVibration deviation: ',ROUND(VIBRATION_DEVIATION,2),
          '\nVibration change over 1 hour: ',ROUND(VIBRATION_CHANGE_1H,2),
          '\nAverage temperature: ',ROUND(AVG_TEMPERATURE,2),' C',
          '\nTemperature deviation: ',ROUND(TEMPERATURE_DEVIATION,2),
          '\nTemperature change over 1 hour: ',ROUND(TEMPERATURE_CHANGE_1H,2),
          '\nRPM standard deviation: ',ROUND(RPM_STDDEV,2),
          '\nPressure deviation: ',ROUND(PRESSURE_DEVIATION,2),
          '\nCurrent deviation: ',ROUND(CURRENT_DEVIATION,2),
          '\nHours since maintenance: ',HOURS_SINCE_MAINTENANCE,
          '\nPrevious failures: ',PREVIOUS_FAILURE_COUNT,
          '\nOEE: ',ROUND(OEE*100,1),'%',
          '\nRecommended action: ',RECOMMENDED_ACTION
        )
      ),
      '\\n',CHR(10)
    ) RCA_EXPLANATION
FROM FORGEIQ.ANALYTICS.COMMAND_CENTER_RCA;
