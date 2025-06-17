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


# @app.route(route="test_skeleton_soldier")
# @task_output_binding()
# def test_skeleton_soldier(
#     req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
# ):
#     logging.info("start skeleton soldier test")

#     reddit_credentials = load_reddit_credentials()
#     reddit_client = RedditClient(reddit_credentials)

#     new_chapters = []
#     posts = reddit_client.get_posts("SkeletonSoldier")
#     for post in posts:
#         if (
#             is_at_most_one_day_old(post.created_at_datetime.date())
#             and post.flair
#             and post.flair.lower() == "new chapter"
#         ):
#             new_chapters.append(post)

#     if not new_chapters:
#         return

#     tasks = []
#     for chapter in new_chapters:
#         logging.info(
#             f"New chapter found: {chapter.title} at {chapter.created_at_datetime}"
#         )
#         tasks.append(
#             create_task_output_event(
#                 title=f"SkeletonSoldier {chapter.title}",
#                 notes="https://demonicscans.org/manga/Skeleton-Soldier",
#                 tasklist=TaskListType.MANGA,
#             )
#         )

#     if tasks:
#         taskOutput.set(tasks)  # type: ignore

#     return func.HttpResponse("Skeleton Soldier test completed successfully.")


@app.timer_trigger(
    schedule="7 6 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
)
@task_output_binding()
@telegram_output_binding()
def skeleton_soldier_update(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
        logging.info("Starting skeleton soldier update timer function")

        # Use Reddit client approach
        reddit_credentials = load_reddit_credentials()
        reddit_client = RedditClient(reddit_credentials)

        new_chapters = []
        posts = reddit_client.get_posts("SkeletonSoldier")
        for post in posts:
            if (
                is_at_most_one_day_old(post.created_at_datetime.date())
                and post.flair
                and post.flair.lower() == "new chapter"
            ):
                new_chapters.append(post)

        if not new_chapters:
            logging.info("Skeleton Soldier: No update found")
            return

        tasks = []
        for chapter in new_chapters:
            logging.info(
                f"New chapter found: {chapter.title} at {chapter.created_at_datetime}"
            )
            tasks.append(
                create_task_output_event(
                    title=f"SkeletonSoldier {chapter.title}",
                    notes="https://demonicscans.org/manga/Skeleton-Soldier",
                    tasklist=TaskListType.MANGA,
                )
            )

        if tasks:
            taskOutput.set(tasks)  # type: ignore

    except Exception as e:
        logging.error(str(e))
        telegramOutput.set(
            create_telegram_output_event(
                message=f"Error in skeleton_soldier_update: {str(e)}"
            )
        )
