// Optional OpenTelemetry Web tracing bootstrap.
// Activates only if VITE_OTLP_URL is set.

import { WebTracerProvider } from '@opentelemetry/sdk-trace-web'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base'
import { registerInstrumentations } from '@opentelemetry/instrumentation'
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch'

const endpoint = import.meta.env.VITE_OTLP_URL as string | undefined

if (endpoint) {
  const provider = new WebTracerProvider()
  const exporter = new OTLPTraceExporter({ url: `${endpoint.replace(/\/$/, '')}/v1/traces` })
  provider.addSpanProcessor(new SimpleSpanProcessor(exporter))
  provider.register()

  registerInstrumentations({
    instrumentations: [
      new FetchInstrumentation({
        propagateTraceHeaderCorsUrls: [/.*/],
      }),
    ],
  })
}

