# This code is from the CMake FAQ

if (NOT EXISTS "/home/macrodrigues/code/macrodrigues/my_projects/butterfly_detector/app/.buildozer/android/platform/build-armeabi-v7a/build/other_builds/jpeg/armeabi-v7a__ndk_target_21/jpeg/install_manifest.txt")
  message(FATAL_ERROR "Cannot find install manifest: \"/home/macrodrigues/code/macrodrigues/my_projects/butterfly_detector/app/.buildozer/android/platform/build-armeabi-v7a/build/other_builds/jpeg/armeabi-v7a__ndk_target_21/jpeg/install_manifest.txt\"")
endif(NOT EXISTS "/home/macrodrigues/code/macrodrigues/my_projects/butterfly_detector/app/.buildozer/android/platform/build-armeabi-v7a/build/other_builds/jpeg/armeabi-v7a__ndk_target_21/jpeg/install_manifest.txt")

file(READ "/home/macrodrigues/code/macrodrigues/my_projects/butterfly_detector/app/.buildozer/android/platform/build-armeabi-v7a/build/other_builds/jpeg/armeabi-v7a__ndk_target_21/jpeg/install_manifest.txt" files)
string(REGEX REPLACE "\n" ";" files "${files}")
list(REVERSE files)
foreach (file ${files})
  message(STATUS "Uninstalling \"$ENV{DESTDIR}${file}\"")
    if (EXISTS "$ENV{DESTDIR}${file}")
      execute_process(
        COMMAND "/home/macrodrigues/.pyenv/versions/3.9.5/envs/marco_venv/lib/python3.9/site-packages/cmake/data/bin/cmake" -E remove "$ENV{DESTDIR}${file}"
        OUTPUT_VARIABLE rm_out
        RESULT_VARIABLE rm_retval
      )
    if(NOT ${rm_retval} EQUAL 0)
      message(FATAL_ERROR "Problem when removing \"$ENV{DESTDIR}${file}\"")
    endif (NOT ${rm_retval} EQUAL 0)
  else (EXISTS "$ENV{DESTDIR}${file}")
    message(STATUS "File \"$ENV{DESTDIR}${file}\" does not exist.")
  endif (EXISTS "$ENV{DESTDIR}${file}")
endforeach(file)
