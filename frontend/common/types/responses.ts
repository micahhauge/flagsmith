// eslint-disable-next-line @typescript-eslint/no-empty-interface
export type EdgePagedResponse<T> = PagedResponse<T> & {last_evaluated_key?:string, pages?:(string|undefined)[]}
export type PagedResponse<T> = {
  count?: number;
  next?: string;
  previous?: string;
  results: T[];
}
export type FlagsmithValue = string | number | boolean | null
export type SegmentRule = {
  type: string;
  rules: SegmentRule[];
  conditions: {
    operator: string;
    property: string;
    value: FlagsmithValue;
  }[];
}
export type Segment = {
  id: number;
  rules: SegmentRule[];
  uuid: string;
  name: string;
  description: string;
  project: number;
  feature?: number;
}
export type Environment = {
  id: number;
  name: string;
  api_key: string;
  description?: string;
  project: number;
  minimum_change_request_approvals?: number;
  allow_client_traits: boolean;
}
export type Project =  {
  id: number;
  uuid: string;
  name: string;
  organisation: number;
  hide_disabled_flags: boolean;
  enable_dynamo_db: boolean;
  migration_status: string;
  use_edge_identities: boolean;
  prevent_flag_defaults: boolean;
  enable_realtime_updates: boolean;
  environments: Environment[];
}
export type ProjectSummary = Omit<Project, 'environments'>
export type AuditLogItem = {
  id: number;
  created_date: string;
  log: string;
  author?: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  environment?: Environment;
  project: ProjectSummary;
  related_object_id: number;
  related_object_type: string;
  is_system_event: boolean;
}
export type Subscription = {
  id: number;
  uuid: string;
  subscription_id: string|null;
  subscription_date: string;
  plan: string|null;
  max_seats: number;
  max_api_calls: number;
  cancellation_date: string | null;
  customer_id: string;
  payment_method: string;
  notes: string|null;
}

export type Organisation = {
  id: number;
  name: string;
  created_date: string;
  webhook_notification_email: string | null;
  num_seats: number;
  subscription: Subscription;
  role: string;
  persist_trait_data: boolean;
  block_access_to_admin: boolean;
  restrict_project_create_to_admin: boolean;
}
export type Identity = {
  id?: string
  identifier: string
  identity_uuid?: string
}
export type Res = {
  segments: PagedResponse<Segment>;
  segment: {id:string};
  auditLogs: PagedResponse<AuditLogItem>;
  organisations: PagedResponse<Organisation>;
  projects: ProjectSummary[];
  environments: PagedResponse<Environment>;
  organisationUsage: {
    totals: {
      flags: number;
      environmentDocument: number;
      identities: number;
      traits: number;
      total: number;
    };
    events_list: {
      "Environment-document": number|null;
      Flags: number|null;
      Identities: number|null;
      Traits: number|null;
      name: string;
    }[]
  }
  identity: {id:string} //todo: we don't consider this until we migrate identity-store
  identities: EdgePagedResponse<Identity>
  // END OF TYPES
}
