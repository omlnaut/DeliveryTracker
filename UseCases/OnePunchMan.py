import logging

import azure.functions as func

from Infrastructure.google_task.azure_helper import (
    TaskListType,
    create_task_output_event,
    task_output_binding,
)
from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from function_app import app
from shared.AzureHelper.reddit_credentials import load_reddit_credentials
from shared.Reddit import RedditClient
from shared.date_utils import is_at_most_one_day_old


@app.timer_trigger(
    schedule="7 6 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
)
@task_output_binding()
@telegram_output_binding()
def one_punch_man_update(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
        logging.info("Starting One Punch Man update timer function")

        # Use Reddit client approach
        reddit_credentials = load_reddit_credentials()
        reddit_client = RedditClient(reddit_credentials)

        new_chapters = []
        posts = reddit_client.get_posts("OnePunchMan")
        for post in posts:
            if (
                is_at_most_one_day_old(post.created_at_datetime.date())
                and post.flair
                and post.flair.lower() == "murata chapter"
            ):
                new_chapters.append(post)

        if not new_chapters:
            logging.info("One Punch Man: No update found")
            return

        tasks = []
        for chapter in new_chapters:
            logging.info(
                f"New chapter found: {chapter.title} at {chapter.created_at_datetime}"
            )
            tasks.append(
                create_task_output_event(
                    title=f"One Punch Man {chapter.title}",
                    notes="https://onepunch-man.com/manga/",
                    tasklist=TaskListType.MANGA,
                )
            )

        if tasks:
            taskOutput.set(tasks)  # type: ignore

    except Exception as e:
        logging.error(str(e))
        telegramOutput.set(
            create_telegram_output_event(
                message=f"Error in one_punch_man_update: {str(e)}"
            )
        )
