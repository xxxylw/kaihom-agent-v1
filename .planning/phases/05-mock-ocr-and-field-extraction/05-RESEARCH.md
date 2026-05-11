# Phase 5 Research: Mock OCR and Field Extraction

**Phase:** 05 - Mock OCR and Field Extraction  
**Date:** 2026-05-11  
**Status:** Complete

## Research Question

What fields should a logistics order draft schema cover for domestic and international logistics order creation, and how should Phase 5 implement mock OCR extraction without blocking future query/reporting needs?

## Findings

### Common Shipment Creation Fields

Across DHL, FedEx, UPS, Maersk, and Cainiao, shipment/order creation repeatedly needs:

- Sender/shipper identity and address.
- Receiver/consignee identity and address.
- Origin and destination.
- Cargo/goods description.
- Package count, weight, and sometimes dimensions/volume.
- Service/product type and pickup/dropoff information.
- Payment/charge information.
- International/customs fields when cross-border or ocean freight applies.

### Source Notes

- DHL's shipment flow includes address details, shipment details, customs invoice details, packaging, payment, shipping date, product selection, optional services, and pickup/dropoff decisions.
- FedEx Ship API lists required create-shipment inputs including account number, pickup type, service type, packaging type, shipper, recipient, payment type, package weights, and label specification.
- UPS guides users to measure/weight packages, enter origin/destination addresses, choose delivery speed/services, and pay/print labels.
- Maersk booking requires from/to location, service mode, contractual customer, departure date, commodity/cargo details, container type/size, container count, and weight per container.
- Cainiao domestic order/waybill APIs require sender, receiver, package, goods name/count, weight, and order identifiers.

## Recommendation

Phase 5 should implement a typed `OrderDraftPreview` schema covering all agreed logistics fields, but use `required_fields` only for missing-field detection. This supports both domestic and international logistics while keeping Phase 5 focused on deterministic extraction rather than full production order modeling.

## Storage Recommendation

Use JSON storage for the Phase 5 extraction preview because:

- The output is an extraction preview, not a finalized order.
- Field contracts may evolve when real Kaihong API fields become available.
- Extraction evidence and conflicts are semi-structured.
- Current access pattern is by `task_id`, not analytics by field.
- Existing Mock Kaihong draft storage already uses JSON payloads.

However, the implementation must preserve:

- Stable canonical field names.
- Typed values.
- `missing_fields`.
- Field evidence metadata.
- Conflict metadata.

These let a future analytics/reporting phase add queryable projections, normalized tables, or reporting views without redoing extraction semantics.

## Risks

- If field names drift now, future query/reporting will be painful. Mitigation: centralize canonical fields in the Pydantic schema and tests.
- If JSON shape is too loose, downstream clarification and reporting will be fragile. Mitigation: typed schema, not arbitrary dict-only storage.
- If Phase 5 over-normalizes into database columns too early, future Kaihong field mapping changes will cause churn. Mitigation: JSON now, projection later.

## Conclusion

Plan Phase 5 as deterministic extraction with typed schemas and JSON persistence, with an explicit future query/reporting migration path.
