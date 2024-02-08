cmake_minimum_required(VERSION 3.10)
project("New Exchange")

list(APPEND
      FOLDERS
      # 20240122_stl
      # 20240124_complete_search
      # 20240126_divide_and_conquer
      # 20240129_basic_graphs
      20240131_binary_search_trees
      scratch)

foreach(folder IN LISTS FOLDERS)
  add_subdirectory(${folder})
endforeach()
