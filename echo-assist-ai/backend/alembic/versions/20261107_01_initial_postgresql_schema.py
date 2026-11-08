"""Create the initial production schema.

Revision ID: 20261107_01
Revises:
Create Date: 2026-11-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20261107_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("full_name", sa.String(length=120), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("preferred_language", sa.String(length=10), nullable=False, server_default="en"),
            sa.Column("phone_number", sa.String(length=20), nullable=True),
            sa.Column("role", sa.String(length=30), nullable=False, server_default="user"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "user_profiles" not in existing_tables:
        op.create_table(
            "user_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("profile_photo_url", sa.String(length=500), nullable=True),
            sa.Column("date_of_birth", sa.Date(), nullable=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("medical_accessibility_preferences", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
        )

    if "user_settings" not in existing_tables:
        op.create_table(
            "user_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
            sa.Column("voice_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("vibration_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("high_contrast_mode", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("large_text_mode", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("fall_detection_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("fall_detection_countdown_seconds", sa.Integer(), nullable=False, server_default="15"),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("user_id", name="uq_user_settings_user_id"),
        )
        op.create_index("ix_user_settings_id", "user_settings", ["id"])

    if "emergency_contacts" not in existing_tables:
        op.create_table(
            "emergency_contacts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("relationship_type", sa.String(length=50), nullable=False),
            sa.Column("phone_number", sa.String(length=20), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_emergency_contacts_id", "emergency_contacts", ["id"])

    if "devices" not in existing_tables:
        op.create_table(
            "devices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("device_id", sa.String(length=64), nullable=False),
            sa.Column("device_name", sa.String(length=120), nullable=False, server_default="ECHO-CANE"),
            sa.Column("firmware_version", sa.String(length=20), nullable=True),
            sa.Column("last_connected_at", sa.DateTime(), nullable=True),
            sa.Column("connection_status", sa.String(length=20), nullable=False, server_default="disconnected"),
            sa.Column("battery_percent", sa.Float(), nullable=True),
            sa.Column("sensor_health", sa.String(length=20), nullable=False, server_default="unknown"),
            sa.Column("is_simulator", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_devices_id", "devices", ["id"])
        op.create_index("ix_devices_device_id", "devices", ["device_id"], unique=True)

    if "sensor_readings" not in existing_tables:
        op.create_table(
            "sensor_readings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
            sa.Column("ultrasonic_cm", sa.Float(), nullable=True),
            sa.Column("tof_mm", sa.Float(), nullable=True),
            sa.Column("accel_x", sa.Float(), nullable=True),
            sa.Column("accel_y", sa.Float(), nullable=True),
            sa.Column("accel_z", sa.Float(), nullable=True),
            sa.Column("gyro_x", sa.Float(), nullable=True),
            sa.Column("gyro_y", sa.Float(), nullable=True),
            sa.Column("gyro_z", sa.Float(), nullable=True),
            sa.Column("sos_pressed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("battery_percent", sa.Float(), nullable=True),
            sa.Column("device_timestamp", sa.Integer(), nullable=True),
            sa.Column("received_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_sensor_readings_id", "sensor_readings", ["id"])

    if "detection_events" not in existing_tables:
        op.create_table(
            "detection_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("class_name", sa.String(length=50), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("position", sa.String(length=10), nullable=False, server_default="center"),
            sa.Column("bbox_x1", sa.Float(), nullable=True), sa.Column("bbox_y1", sa.Float(), nullable=True),
            sa.Column("bbox_x2", sa.Float(), nullable=True), sa.Column("bbox_y2", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_detection_events_id", "detection_events", ["id"])

    if "risk_events" not in existing_tables:
        op.create_table(
            "risk_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("object_name", sa.String(length=50), nullable=False),
            sa.Column("fused_distance_m", sa.Float(), nullable=False),
            sa.Column("direction", sa.String(length=10), nullable=False, server_default="center"),
            sa.Column("risk_level", sa.String(length=10), nullable=False),
            sa.Column("message", sa.String(length=200), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_risk_events_id", "risk_events", ["id"])

    if "emergency_events" not in existing_tables:
        op.create_table(
            "emergency_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("event_type", sa.String(length=30), nullable=False),
            sa.Column("latitude", sa.Float(), nullable=True), sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
            sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("resolved_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_emergency_events_id", "emergency_events", ["id"])
        op.create_index("ix_emergency_events_user_id", "emergency_events", ["user_id"])

    if "navigation_routes" not in existing_tables:
        op.create_table(
            "navigation_routes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("route_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("destination", sa.String(length=255), nullable=False),
            sa.Column("origin_lat", sa.Float(), nullable=False), sa.Column("origin_lng", sa.Float(), nullable=False),
            sa.Column("destination_lat", sa.Float(), nullable=False), sa.Column("destination_lng", sa.Float(), nullable=False),
            sa.Column("total_distance_m", sa.Float(), nullable=False), sa.Column("estimated_time_minutes", sa.Float(), nullable=False),
            sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_instruction", sa.Text(), nullable=True),
            sa.Column("navigation_status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
            sa.Column("provider", sa.String(length=100), nullable=True), sa.Column("profile", sa.String(length=100), nullable=True),
            sa.Column("geometry", sa.JSON(), nullable=False), sa.Column("steps", sa.JSON(), nullable=False),
            sa.Column("provider_steps", sa.JSON(), nullable=False),
            sa.Column("previous_route_id", sa.String(length=36), nullable=True),
            sa.Column("replaced_by_route_id", sa.String(length=36), nullable=True),
            sa.Column("mock_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("rerouted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_navigation_routes_id", "navigation_routes", ["id"])
        op.create_index("ix_navigation_routes_route_id", "navigation_routes", ["route_id"], unique=True)
        op.create_index("ix_navigation_routes_user_id", "navigation_routes", ["user_id"])
        op.create_index("ix_navigation_routes_navigation_status", "navigation_routes", ["navigation_status"])
        op.create_index("ix_navigation_routes_previous_route_id", "navigation_routes", ["previous_route_id"])

    if "saved_locations" not in existing_tables:
        op.create_table(
            "saved_locations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("label", sa.String(length=120), nullable=False), sa.Column("address", sa.String(length=255), nullable=False),
            sa.Column("latitude", sa.Float(), nullable=False), sa.Column("longitude", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_saved_locations_id", "saved_locations", ["id"])

    if "notifications" not in existing_tables:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("sos_alert_id", sa.Integer(), sa.ForeignKey("emergency_events.id"), nullable=True),
            sa.Column("channel", sa.String(length=20), nullable=False), sa.Column("recipient", sa.String(length=255), nullable=True),
            sa.Column("title", sa.String(length=200), nullable=False), sa.Column("message", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("provider_message_id", sa.String(length=255), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True), sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("delivered_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    if "system_logs" not in existing_tables:
        op.create_table(
            "system_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("event_type", sa.String(length=100), nullable=False), sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
            sa.Column("message", sa.Text(), nullable=False), sa.Column("context_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_system_logs_user_id", "system_logs", ["user_id"])
        op.create_index("ix_system_logs_event_type", "system_logs", ["event_type"])
        op.create_index("ix_system_logs_created_at", "system_logs", ["created_at"])


def downgrade() -> None:
    for table_name in (
        "system_logs", "notifications", "saved_locations", "navigation_routes", "emergency_events",
        "risk_events", "detection_events", "sensor_readings", "devices", "emergency_contacts",
        "user_settings", "user_profiles", "users",
    ):
        op.drop_table(table_name)
