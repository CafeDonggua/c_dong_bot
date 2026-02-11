from dongdong_bot.agent.cron_parser import CronParser


def test_cron_list_with_status_filter():
    parser = CronParser()

    command = parser.parse("/cron list scheduled")

    assert command is not None
    assert command.valid
    assert command.action == "list"
    assert command.status_filter == "scheduled"


def test_cron_manage_actions_require_valid_task_id():
    parser = CronParser()

    remove_cmd = parser.parse("/cron remove task1234")
    enable_cmd = parser.parse("/cron enable task1234")
    disable_cmd = parser.parse("/cron disable task1234")
    invalid_cmd = parser.parse("/cron remove !!")

    assert remove_cmd is not None and remove_cmd.valid and remove_cmd.task_id == "task1234"
    assert enable_cmd is not None and enable_cmd.valid and enable_cmd.enabled is True
    assert disable_cmd is not None and disable_cmd.valid and disable_cmd.enabled is False

    assert invalid_cmd is not None
    assert not invalid_cmd.valid
    assert "task_id 格式不正確" in invalid_cmd.errors[0]
